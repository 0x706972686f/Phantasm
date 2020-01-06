"""
Phantasm

Phantasm is a library that has been developed for programmatic testing of
Splunk Phantom. In doing so we can use test-driven development to test playbooks

The class will allow you to create containers and artifacts, as well as allow
you to run playbooks, individual actions, upload files to the vault, promote or
demote a container to a case, delete a container, and retrieve the JSON data
relating to all the actions.

Refer to demo.py to showcase how to use the library, or the test_example.py
file for a demonstration on how to use with pytest

Installation:
    pip install -r requirements.txt

Future Planned Improvements:
    - Finish modifying conftest.py to use webhooks to post the outcome somewhere
    - Provide a function to list the users, using the following API endpoint:
        /rest/ph_user?_filter_type__in=["normal","automation"]&page_size=0
    - Provide a function to list custom lists, using the following API endpoint:
        /rest/decided_list

Changelog:
    2019-11-15  -   Added additional functions that help with identifying playbooks
                    impacted by system failures, provide further information
                    regarding playbooks, and can be used to work backwards (from
                    a playbook identifying the container associated and more).
    2019-06-30  -   Re-engineered the entire thing, including converting it from
                    standalone functions to a class, including custom exceptions
                    simplifying the code and documenting it.
"""
__author__ = "Sean Breen"
__credits__ = ["Christopher Hanlen","John Murphy","Sean Breen","Rex Chen"]
__license__ = "GNU AGPLv3"
__version__ = "2.0.0"
__maintainer__ = "sean@shadow.engineering"
__email__ = "sean@shadow.engineering"

import os, sys, csv
import json
import requests
import time
import logging

# Phantom uses self signed certificates, so need to disable warnings
requests.packages.urllib3.disable_warnings()

# Setting up a Debug Logger
logger = logging.getLogger(__name__)


"""
Custom Exception Handling
"""
class phantomException(Exception):
    pass

class containerException(phantomException):
    pass

class artifactException(containerException):
    pass

class playbookException(containerException):
    pass

class actionException(containerException):
    pass



"""
Class: phantasm

Description:
    Phantasm is the class for developing and testing Splunk Phantom playbook
    development. The class will allow you to create containers and artifacts,
    as well as allow you to run playbooks, individual actions, upload files to
    the vault, promote or demote a container to a case, delete a container, and
    retrieve the JSON data relating to all the actions.

Container Functions:
    create_container                    - Creates a new container
    update_container_status             - Updates the container status
    update_container_tags               - Adds a tag to the container
    get_last_created_container          - Identifies the most recently created container
    get_container_artifacts             - Retrieves the list of artifacts currently in the container
    promote_container_to_case           - Promotes the current container to a case
    demote_case_to_container            - Demotes the current case to a container
    delete_container                    - Deletes a container

Artifact Functions:
    add_artifact                        - Adds an artifact to a container
    get_last_created_artifact           - Identifies the most recently created artifact

File Functions:
    upload_file_to_phantom              - Uploads a file to a container    

Playbook Functions:
    run_playbook                        - Runs a playbook against a container
    get_playbook_results                - Retrieves the status of the playbook
    get_playbook_action_results         - Retrieves the status of the last run action in the playbook
    get_playbook_information            - Retrieves the information relating to a playbook
    get_last_run_playbook_information   - Retrieves the information relating to the last executed playbook
    alter_playbook_active_state         - Activates/Deactives a playbook
    get_system_failure_impacted_playbooks - Identifies playbooks that didn't execute due to a system failure
    get_system_failure_pending_playbooks - Identifies playbooks that were pending execution before a system failure

Action Functions:
    get_application_id                  - Retrieves an application id
    run_action                          - Run an action
    get_action_results                  - Retrieve the results of an action
    get_action_run_data                 - Retrieve the data of the action

Misc Functions:
    get_jira_ticket_data                - Runs an action to retrieve all JIRA tickets.
"""
class phantasm(object):
    def __init__(self):
        '''Setting Global Variables'''
        import configparser
        configuration=configparser.ConfigParser()
        configuration.read('config.ini')
        self._phantom_server_address = configuration.get('PHANTOM', 'server_address')
        self._phantom_auth_token = configuration.get('PHANTOM', 'auth_token')
        self._url_headers = {'ph-auth-token': self._phantom_auth_token}

        '''Setting the Requests Components'''
        self._sess = requests.Session()
        self._sess.headers = self._url_headers
        self._sess.hooks = {'response': self._hook_response}

        '''Setting Container Variables'''
        self._container_name = ""
        self._container_label = ""
        self._source_identifier = ""

        '''Setting Artifact Variables'''
        self._artifact_id = []
        self._artifact_label = []
        self._artifact_name = []

        '''Setting File Variables'''
        self._file_id = []
        self._file_name = []

        '''Setting Playbook Variables'''
        self._playbook_run_id = []
        self._playbook_name = []

        '''Setting Misc Variables'''
        self._last_run_product_name = ''
        self._last_run_application_id = ''
        self._last_run_action_id = ''
        self._last_run_action_name = ''
        self._user_id = ''
        self._password = ''

    """
    def __exit__(self):
        '''
        Can overwrite the __exit__ function to set the container to be resolved, and add a tag of 'tested'
        '''
    """

    def __str__(self):
        '''
        Overwrites the string class to return the documentation regarding the object.
        '''
        return phantomcontainer.__doc__

    """"
    HTTP: Functions
    """"
    @staticmethod
    def _hook_response(post_response, *args, **kwargs):
        '''
        Function: _hook_response

        Description:
        Used for debugging the actions being completed
        '''
        post_response.raise_for_status()
        logger.debug("Request: {0}\nResponse: {1}".format(post_response.url, post_response.json()))

    def _url(self, url_path, filter=[], page_number=0, page_size=0):
        '''
        Function: _url

        Description:
        A function to poll the ongoing action and confirm if it's completed.

        Args:
            url_path (str)                  - The URL path: https://phantom.local/rest/<path>
            (optional) filter (array)       - Optional filters to add for further information: https://phantom.local/rest/app_run?_filter_playbook_run_id=<playbook_id>&_filter_action="<action>"&include_expensive'

        Returns:
            (str)                           - The string for the URL
        '''
        url_path += '?page={}&page_size={}'.format(page_number,page_size)
        if filter:
            """
            Add query string for filtered actions
            e.g.    'https://phantom.local/rest/app_run?_filter_playbook_run_id=<playbook_id>&_filter_action="<action>"&include_expensive'
            """
            filter_query_string="?"
            for action in filter:
                filter_query_string += '&_filter_{}'.format(action)
        else:
            filter_query_string=""
        url_path += '&include_expensive'
        return self._phantom_server_address + url_path + filter_query_string

    def _wait(self, url, interval=1, max_attempts=10):
        '''
        Function: _wait

        Description:
        A function to poll the ongoing action and confirm if it's completed.

        Args:
            url (str)                       - The URL to poll
            (optional) interval (int)       - The period of time to wait until polling (by default 1 second)
            (optional) max_attempts (int)   - The number of attempts to poll

        Returns:
            app_runs (json)                 - The JSON data of the action
        '''
        for count in range(max_attempts):
            post_response = self._sess.get(url)
            status = post_response.json().get("status")
            success = post_response.json().get("success")
            count = post_response.json().get("count")
            if status is in ['failed', 'success', 'new', 'closed', 'open']:
                return post_response.json()
            elif status is in ['pending', 'running'']:
                time.sleep(interval)
                continue
            elif success:
                return post_response.json()
            elif count:
                return post_response.json()
            else:
                raise ValueError('Wrong return status: {0}'.format(status))
                logger.debug("Action is still in {} status, wait timeout.".format(post_response.json()['status']))
                return None

    """
    Container: Functions
    """
    def create_container(self,name="TEST - Default Name",artifacts=[],custom_fields={},data={},description="This originated from a PyTest Case",label="events",run_automation=True,sensitivity="white",severity="low",source_data_identifier="",status="new",tags=[]):
        '''
        Function: create_container

        Description:
        Creates a new container

        label="events",run_automation=True,sensitivity="white",severity="low",source_data_identifier="",status="new",tags=[]):


        Args:
            name (str)                                  - The name of the container
            artifacts (bool)                            - An array of artifacts to add
            custom_fields (dict)                        - The custom fields to include
            data (dict)                                 - Data to include
            (optional) description (str)                - The description of the container
            (optional) label (str)                      - The label of the container
            (optional) run_automation (bool)            - Whether to run automation or not, required to be true
            (optional) sensitivity (string)             - The TLP sensitivity of the container
            (optional) severity (string)                - The severity of the data
            (optional) source_data_identifier (str)     - The identifier of the source
            (optional) status (str)                     - The Status of the container
            (optional) tags (dict)                      - Any tags to include in the container

        Returns:
            Response (json)                 - The JSON data of the action
        '''
        post_data = {}
        post_data['artifacts'] = artifacts
        post_data['custom_fields'] = custom_fields
        post_data['data'] = data
        post_data['description'] = description
        post_data['label'] = label
        post_data['name'] = name
        post_data['run_automation'] = run_automation
        post_data['sensitivity'] = sensitivity
        post_data['severity'] = severity
        post_data['source_data_identifier'] = source_data_identifier
        post_data['status'] = status
        post_data['tags'] = tags

        post_response = self._sess.post(self._url('container'), json=post_data)
        self._set_container_id(post_response.json().get('id'))
        return post_response.json()

    def update_container_status(self,status="resolved",container_id=None):
        '''
        Function: update_container_status

        Description:
        Promotes the current container to a case, built in to the phantom case management system. It uses the template of another already existing case.

        Args:
            (optional) status (str)         - The Status to update the container to, defaults to resolved
            (optional) contianer_id (str)   - The Container ID, defaults to current container

        Returns:
            Response (json)                 - The JSON data of the action
        '''
        if not container_id:
            container_id = self._get_container_id()
        post_data = {}
        post_data['container_id'] = container_id
        post_data['status'] = status
        url = self._url('container/{}'.format(container_id))
        post_response = self._sess.post(url)

        return post_response.json()


    def update_container_tags(self,tags=["Testing"],container_id=None):
        '''
        Function: update_container_tags

        Description:
        Promotes the current container to a case, built in to the phantom case management system. It uses the template of another already existing case.

        Args:
            (optional) tags (dict)          - A dictionary of tags to add to the container.
            (optional) container_id (str)   - The Container ID, defaults to current container

        Returns:
            Response (json)                 - The JSON data of the action
        '''
        if not container_id:
            container_id = self._get_container_id()
        post_data = {}
        post_data['container_id'] = container_id
        post_data['tags'] = tags
        url = self._url('container/{}'.format(container_id))
        post_response = self._sess.post(url)

        return post_response.json()

    def get_last_created_container(self, container_tag=""):
        '''
        Function: get_last_created_container

        Description:
        Identifies the most recently created container. You can provide the string for the container tag to identify more specific containers.

        Args:
            (optional) container_tag (str)  - The tag of a container to filter on.

        Returns:
            Response (json)                 - The JSON data of the action
        '''
        filters = [] 
        filters.append('tags__icontains="{}"&sort=id&order=desc'.format(container_tag))
        url = self._url('container',page_size=1,filters=filters)
        post_response = self._sess.get(url)

        return post_response.json()


    def get_container_artifacts(self, container_id=None):
        '''
        Function: get_container_artifacts

        Description:
        Promotes the current container to a case, built in to the phantom case management system. It uses the template of another already existing case.

        Args:
            template_name (str)             - The name of the Phantom case template, which will be used as the basis for the case.
            (optional) container_id (str)   - The Container ID to promote (defaults to existing case if there is one)

        Returns:
            Response (json)                 - The JSON data of the action
        '''
        if not container_id:
            container_id = self._get_container_id()
        filter = []
        filter.append('container={}'.format(container_id))
        post_response = self._sess.post(self._url('artifact', filter))

        return post_response.json()

    def promote_container_to_case(self, template_name, container_id=None):
        '''
        Function: promote_container_to_case

        Description:
        Promotes the current container to a case, built in to the phantom case management system. It uses the template of another already existing case.

        Args:
            template_name (str)             - The name of the Phantom case template, which will be used as the basis for the case.
            (optional) container_id (str)   - The Container ID to promote (defaults to existing case if there is one)

        Returns:
            Response (json)                 - The JSON data of the action
        '''
        if not container_id:
            container_id = self._get_container_id()
        # First we need to get the template id, based on the template name
        url = self._url('name="{}"').format(template_name)
        post_response = self._sess.post(url)

        response_json = post_response.json()

        template_id = response_json['data'][0]['id']
        self._set_template_id(template_id)
        self._set_template_name(template_name)

        # Now that we know the template_id we can get the promote a container to a case
        post_data = {}
        post_data['container_type'] = 'case'
        post_data['template_id'] = template_id
        url = self._url('rest/container/{}').format(container_id)
        post_response = self._sess.post(url)
        self._set_case_id(post_response.json().get('id'))

        return post_response.json()

    def demote_case_to_container(self):
        '''
        Function: demote_case_to_container

        Description:
        Demotes a case back to a container

        Returns:
            Response (json)                - The JSON data of the action
        '''
        post_data = dict()
        post_data['container_type'] = 'default'
        post_json = json.dumps(post_data)

        url_string = 'container/{}'.format(self._container_id)
        post_response = self._sess.post(self._url(url_string), json=post_json)

        self._set_template_id('0')
        self._set_template_name('None')
        self._set_case_id('0')

        return post_response.json()

    def delete_container(self, userid, password, container_id=None):
        '''
        Function: delete_container

        Description:
        Deletes the container created by this object. It does this by conducting a HTTP DELETE to the Phantom API, using the container ID.

        Args:
            userid (str)                - The userid to be used to authenticate.
            password (str)              - The password to be used to authenticate.
            (optional) container_id (Str) - The ID of the Container to delete

        Returns:
            Response (json)             - The JSON data of the action
        '''
        if not container_id:
            container_id = self._get_container_id()
        url_string = 'container/{}'.format(container_id)
        post_response = self._sess.delete(self._url(url_string), auth=(userid, password))
        return post_response.json()

    """
    Container: Setting and Getting Variables
    """
    def _set_container_id(self, phantom_container_id):
        self._container_id = phantom_container_id

    def _get_container_id(self):
        return self._container_id

    def _set_container_name(self, phantom_container_name):
        self._container_name = phantom_container_name

    def _get_container_name(self):
        return self._container_name

    def _set_source_identifier(self, source_identifier):
        self._source_identifier = source_identifier

    def _get_source_identifier(self):
        return self._source_identifier

    def _set_template_id(self, template_id):
        self._template_id = template_id

    def _get_template_id(self):
        return self._template_id

    def _set_template_name(self, template_name):
        self._template_name = template_name

    def _get_template_name(self):
        return self._template_name

    def _set_case_id(self, case_id):
        self._case_id = case_id

    def _get_case_id(self):
        return self._case_id

    def _set_user_id(self, user_id):
        self._user_id = user_id

    def _get_user_id(self):
        return self._user_id

    def _set_password(self, password):
        self._password = password

    def _get_password(self):
        return self._password


    """
    Container: Properties
    """
    source_identifier = property(_get_source_identifier, _set_source_identifier)
    container_id = property(_get_container_id, _set_container_id)
    container_name = property(_get_container_name, _set_container_name)
    template_id = property(_get_template_id, _set_template_id)
    template_name = property(_get_template_name, _set_template_name)
    case_id = property(_get_case_id, _set_case_id)
    user_id = property(_get_user_id, _set_user_id)
    password = property(_get_password, _set_password)


    """
    Artifact: Functions
    """
    def add_artifact(self,container_id=None,cef={},cef_types={},data={},description="TESTING: Creating artifact for testing purposes",label="events",name="Test Artifact",run_automation=True,severity="low",source_data_identifier="", tags=[]):
        '''
        Function: add_artifacts

        Description:
        Add an artifact to a case, can be run multiple times to add additional artifacts.

        Args:
            (optional) container_id (str)               - The container ID to add an artifact to
            cef (dict)                                  - The CEF dictionary of the artifact
            cef_types (dict)                            - A dictionary of the CEF types
            data (dict)                                 - The data of the artifact
            (optional) description (str)                - A description of the artifact
            (optional) label (str)                      - The label to add to the artifact
            (optional) name (str)                       - The name of the artifact
            (optional) run_automation (bool)            - Whether to run the automation or not
            (optional) severity (str)                   - The severity of the artifact
            (optional) source_data_identifier (str)     - The source_data_identifier string
            (optional) tags (array)                     - The tags to add to the artifact

        Returns:
            Response (json)                - The JSON data of the action
        '''
        if not container_id:
            container_id = self._get_container_id()

        post_data = {}
        post_data['cef'] = cef
        post_data['cef_types'] = cef_types
        post_data['container_id'] = container_id
        post_data['data'] = data
        post_data['description'] = description
        post_data['label'] = label
        post_data['name'] = name
        post_data['run_automation'] = run_automation
        post_data['severity'] = severity
        post_data['source_data_identifier'] = source_data_identifier
        post_data['tags'] = tags

        post_response = self._sess.post(self.url('artifact'), json=post_data)
        self._set_artifact_id(post_response.json().get('id'))
        self._set_artifact_name(name)

        return post_response.json()

    
    def get_last_created_artifact(self, artifact_tag=""):
        '''
        Function: get_last_created_artifact

        Description:
        Identifies the most recently created artifact. You can provide the string for the artifact tag to identify more specific artifacts.

        Args:
            (optional) artifact_tag (str)   - The tag of a artifact to filter on.

        Returns:
            Response (json)                 - The JSON data of the action
        '''
        filters = [] 
        filters.append('tags__icontains="{}"&sort=id&order=desc'.format(container_tag))
        url = self._url('artifact',page_size=1,filters=filters)
        post_response = self._sess.get(url)

        return post_response.json()

    """
    Artifact: Setting and Getting Variables
    """
    def _set_artifact_id(self, phantom_artifact_id):
        self._artifact_id.append(phantom_artifact_id)

    def _get_artifact_id(self):
        return self._artifact_id

    def _set_artifact_name(self, phantom_artifact_name):
        self._artifact_name.append(phantom_artifact_name)

    def _get_artifact_name(self):
        return self._artifact_name

    """
    Artifact: Properties
    """
    artifact_id = property(_get_artifact_id, _set_artifact_id)
    artifact_name = property(_get_artifact_name, _set_artifact_name)


    """
    Files: Functions
    """
    def upload_file_to_phantom(self, file_name, container_id=None):
        '''
        Function: upload_file_to_phantom

        Description:
        Uploads a file to the vault of the container.

        Args:
            file_name (str)     - The path and filename of the file to be uploaded.
            (optional) container_id (str)       - The ID of the container

        Returns:
            Response (json)                - The JSON data of the action
        '''
        if not container_id:
            container_id = self._get_container_id()

        if os.path.exists(file_name):
            with open(filename, 'rb') as imported_file:
                try:
                    file_contents = imported_file.read()
                except IOError as read_error:
                    print('Failed to Read File ({}): {}').format(read_error.errno, read_error.strerror)
                except:
                    print('Unexpected Error: {}').format(sys.exc_info()[0])
            if file_contents:
                serialised_contents = base64.b64encode(file_contents).decode()

                post_data = dict()
                post_data['container_id'] = container_id
                post_data['file_content'] = serialised_contents
                post_data['file_name'] = file_name
                post_data['metadata'] = "{'contains': ['vault id']}"

                post_json = json.dumps(post_data)

                post_response = self._sess.post(self._url('container_attachment'), json=post_json)
                self._set_file_id(response_to_post.json().get('id'))
                self._set_file_name(file_name)
                return post_response.json()
            else:
                return None


    """
    Files: Setting and Getting Variables
    """
    def _set_file_id(self, phantom_file_id):
        self._file_id.append(phantom_file_id)

    def _get_file_id(self):
        return self._file_id

    def _set_file_name(self, phantom_file_name):
        self._file_name.append(phantom_file_name)

    def _get_file_name(self):
        return self._file_name

    """
    File: Properties
    """
    file_id = property(_get_file_id, _set_file_id)
    file_name = property(_get_file_name, _set_file_name)

    """
    Playbooks: Functions
    """
    def run_playbook(self, playbook_name, container_id=None, scope='new', run_confirmation=True):
        '''
        Function: run_playbook

        Description:
        Run's a Phantom playbook against the container.

        Args:
            playbook_name (str)                 - The name of the playbook to run
            (optional) container_id (str)       - The ID of the container
            (optional) scope (str)              - The phantom scope to run as, defaults to 'new'
            (optional) run_confirmation (bool)  - The confirmation to run the playbook, defaults to 'false'

        Returns:
            Response (json)                - The JSON data of the action
        '''
        if not container_id:
            container_id = self._get_container_id()

        post_data = dict()
        post_data['container_id'] = container_id
        post_data['playbook_id'] = playbook_name
        post_data['scope'] = scope
        post_data['run'] = run_confirmation

        post_json = json.dumps(post_data)

        post_response = self._sess.post(self._url('playbook_run'), json=post_json)
        self._set_playbook_run_id(post_response.json().get('playbook_run_id'))
        self._set_playbook_name(playbook_name)

        return post_response.json()

    def get_playbook_results(self, playbook_id=None, wait=True, interval=1, max_attempts=10):
        '''
        Function: get_playbook_results

        Description:
        Retrieves the status of a Phantom Playbook. By default will return the status of the last run playbook.

        Args:
            (optional) playbook_id (str)   - The Phantom Playbook ID to run against, by default will run against the last run playbook.
            (optional) wait (bool)         - Whether the playbook should wait until it's completed
            (optional) interval (int)      - The period between polling
            (optional) max_attempts (int)  - The amount of times to poll

        Returns:
            Response (json)                - The JSON data of the action
        '''
        if not playbook_id:
            playbook_id = self._playbook_run_id[-1]

        url = self._url('playbook_run/{}'.format(playbook_id))
        get_response = self._sess.get(url)

        return get_response.json()

    def get_playbook_action_results(self, action, playbook_id=None, wait=True, interval=1, max_attempts=10):
        '''
        Function: get_playbook_action_results

        Description:
        Retrieves the status of the action of a Phantom Playbook. By default will return the status of the last run playbook.

        Args:
            action (str)                   - The name of the action that was run
            (optional) playbook_id (str)   - The Phantom Playbook ID to run against, by default will run against the last run playbook.
            (optional) wait (bool)         - Whether the playbook should wait until it's completed
            (optional) interval (int)      - The period between polling
            (optional) max_attempts (int)  - The amount of times to poll

        Returns:
            Response (json)                - The JSON data of the action
        '''
        if playbook_id is None:
            playbook_id = self._playbook_run_id[-1]

        filters = []
        filters.append("playbook_run_id={}".format(playbook_id))
        filters.append('action="{}"'.format(action))
        url = self._url("app_run", filters=filters)

        post_response = self._sess.get(url)
        if wait:
            return self._wait(url, interval, max_attempts)
        else:
            return post_response.json()

    def get_playbook_information(self,playbook_name=""):
        '''
        Function: get_playbook_information

        Description:
        Returns all of the information relating to a playbook, including the container ID that the playbook ran against.

        Args:
            (optional) playbook_name (str) - The name of the playbook to return the information of.

        Returns:
            Response (json)                - The JSON data of the action
        '''
        if not playbook_name:
            playbook_name = self._playbook_name
        filters = []
        filters.append('name__icontainers="{}"&order=desc'.format(playbook_name))
        url = self._url('playbook_run',page_size=1,filters=filters)
        post_response = self._sess.get(url)
        return post_response.json()

    def get_last_run_playbook_information(self,container_id=None,playbook_name=None,wait=True,interval=1,max_attempts=10):
        '''
        Function: get_last_run_playbook_information

        Description:
        Returns all of the information relating to the last executed playbook. It can be filtered to the last run playbook against a container, the last run playbook based by name or just the last run playbook.

        Args:
            (optional) container_id (str)  - The Container ID to use for filtering the playbook.
            (optional) playbook_name (str) - The name of the playbook to return the information of.

        Returns:
            Response (json)                - The JSON data of the action
        '''
        filters = []
        if container_id:
            filters.append('container_id="{}"&order=desc'.format(container_id))
            url = self._url("playbook_run",page_size=1,filters=filters)
            post_response = self._sess.get(url)
            if wait:
                return self._wait(url, interval, max_attempts)
            else:
                return post_response.json()
        elif playbook_name:
            filters.append('message__icontains="{}"&order=desc'.format(playbook_name))
            url = self._url("playbook_run",page_size=1,filters=filters)
            post_response = self._sess.get(url)
            if wait:
                return self._wait(url, interval, max_attempts)
            else:
                return post_response.json()
        else:
            url = self._url("playbook_run",page_size=1,filters=filters)
            post_response = self._sess.get(url)
            if wait:
                return self._wait(url, interval, max_attempts)
            else:
                return post_response.json()

    def alter_playbook_active_state(self, playbook_id=None, active=False, cancel_runs=False):
        '''
        Function: alter_playbook_active_state

        Description:
        Enables the playbook to be active or inactive. An active playbook will automatically monitor a label and trigger when an event is supplied on that label.

        Args:
            (optional) playbook_id (str)   - The Phantom Playbook ID to run against, by default will run against the last run playbook.
            (optional) active (bool)       - Whether to set the playbook as active (True), or inactive (False)
            (optional) cancel_runs (bool)  - Whether to cancel any existing playbook executions that were pending

        Returns:
            Response (json)                - The JSON data of the action
        '''
        if playbook_id is None:
            playbook_id = self._playbook_run_id[-1]

        post_data = {}
        post_data['active'] = active
        post_data['cancel_runs'] = cancel_runs

        url = self._url("playbook/{}".format(playbook_id))
        post_response = self._sess.post(url, json=post_data)

        return post_response.json()

    def get_system_failure_impacted_playbooks(self,start_date=None,end_date=None):
        '''
        Function: get_system_failure_impacted_playbooks

        Description:
        Identifies playbooks that didn't complete executing due to a system failure in Phantom.
            /rest/playbook_run?page_size=0&_filter_status="failed"&sort=id&order=desc&_filter_message__contains="system/daemon start"&_filter_create_time__range("2019-03-11","2013-04-11")

        Args:
            (optional) start_date (str)    - The starting date to begin filtering the playbooks by
            (optional) end_date (str)      - The end date to filter the playbooks by

        Returns:
            Response (json)                - The JSON data of the action
        '''
        filters = []
        filters.append('status="failed"&sort=id&order=desc')
        filters.append('message__contains="system/daemon start"')
        if start_date and end_date:
            filters.append('create_time__range("{}","{}")'.format(start_date,end_date))
        
        url = self._url("playbook_run",page_size=0,filters=filters)
        post_response = self._sess.get(url)

        return post_response.json()    

        r = self.query(query_type="playbook_run",page_size=0,filters=filters,wait=False)

    def get_system_failure_pending_playbooks(self,start_date=None,end_date=None):
        '''
        Function: get_system_failure_impacted_playbooks

        Description:
        Identifies playbooks that were pending execution, but did not get to begin due to a failure in Phantom. These playbooks never would have executed post-recovery.
            /rest/container?page_size=0&sort=id&order=desc&_filter_playbookrun__container__isnull=True&_filter_create_time__range("2019-03-11","2019-04-11")0

        Args:
            (optional) start_date (str)    - The starting date to begin filtering the playbooks by
            (optional) end_date (str)      - The end date to filter the playbooks by

        Returns:
            Response (json)                - The JSON data of the action
        '''
        filters = []
        filters.append('playbookrun__container__isnull=True&sort=id&order=desc')
        if start_date and end_date:
            filters.append('create_time__range("{}","{}")'.format(start_date,end_date))
        url = self._url("container",page_size=0,filters=filters)
        post_response = self._sess.get(url)

        return post_response.json()    

        r = self.query(query_type="playbook_run",page_size=0,filters=filters,wait=False)     

    """
    Playbooks: Setting and Getting Variables
    """
    def _set_playbook_run_id(self, phantom_playbook_run_id):
        self._playbook_run_id.append(phantom_playbook_run_id)

    def _get_playbook_run_id(self):
        return self._playbook_run_id

    def _set_playbook_name(self, phantom_playbook_name):
        self._playbook_name.append(phantom_playbook_name)

    def _get_playbook_name(self):
        return self._playbook_name

    """
    Playbooks: Properties
    """
    playbook_run_id = property(_get_file_id, _set_file_id)
    playbook_name = property(_get_file_name, _set_file_name)


    """
    Actions: Functions
    """
    def get_application_id(self, application_asset_name):
        '''
        Function: get_application_id

        Description:
        Retrieves the application ID for a known Application name.

        Args:
            application_asset_name (str)        - The name of the Phantom App to look up, will return the ID for it.

        Returns:
            response (json)                     - The JSON data of the action
        '''
        product_filters = []
        product_filters.append('name="{}"'.format(application_asset_name))
        url = self._url("asset", filters=product_filters)
        post_response = self._sess.post(url)

        product_name = post_response.json()['data'][0]['product_name']
        self._set_last_run_product_name(product_name)

        app_filter = []
        app_filter.append('product_name="{}"'.format(product_name))
        url = self._url("asset", filters=app_filter)
        post_response = self._sess.post(url)

        application_id = post_response.json()['data'][0]['id']
        self._set_last_run_application_id(application_id)

        return post_response.json()

    def run_action(self, container_id=None, action_name, asset_name, parameters):
        '''
        Function: run_action

        Description:
        Runs an individual action of an App (e.g: the 'send email' action of the Phantom SMTP asset.)

        Args:
            action_name (str)               - The name of the action to undertake.
            asset_name (str)                - The name of the asset. An asset is an instance of an Application.
            parameters (str)                - The parameters to pass to the action to be run.
            (optional) container_id (str)   - The container ID (defaults to the current container ID)

        Returns:
            Response (json)                 - The JSON data of the action
        '''
        if not container_id:
            container_id = self._get_container_id()

        self.get_application_id(asset_name)
        application_id = self._get_last_run_application_id()

        post_url = 'https://{}/rest/action_run'.format(self._phantom_server_address)

        post_data = {}
        post_data['action'] = action_name
        post_data['container_id'] = container_id
        post_data['name'] = asset_name
        post_data['targets'] = "[{'assets': [{}], 'parameters': {}, 'app_id': {} }]".format(asset_name, parameters, application_id)
        post_json = json.dumps(post_data)

        post_response = self._sess.post('action_run', json=post_json)

        self._set_last_run_action_id(post_response.json().get('action_run_id'))
        self._set_last_run_action_name(action_name)

        return post_response.json()

    def get_action_results(self,action_id=None, wait=True, interval=1, max_attempts=10):
        '''
        Function: get_action_results

        Description:
        Runs an individual action, and returns the action response.

        Args:
            (optional) action_id (str)   - The Action ID to be run against, by default will run against the last provided action.
            (optional) wait (bool)         - Whether the playbook should wait until it's completed
            (optional) interval (int)      - The period between polling
            (optional) max_attempts (int)  - The amount of times to poll

        Returns:
            Response (json)                - The JSON data of the action
        '''
        if action_id is None:
            action_id = self._get_last_run_action_id()

        url = self._url("action_run/{}".format(action_id))
        post_response = self._sess.get(url)
        if wait:
            return self._wait(url, interval, max_attempts)
        else:
            return post_response.json()

    def get_action_run_data(self, action_run_id=None, wait=True, interval=1, max_attempts=10):
        '''
        Function: get_action_run_data

        Description:
        Gets the detailed json information relating to a recently run action

        Args:
            (optional) action_id (str)   - The Action ID to be run against, by default will run against the last provided action.
            (optional) wait (bool)         - Whether the playbook should wait until it's completed
            (optional) interval (int)      - The period between polling
            (optional) max_attempts (int)  - The amount of times to poll

        Returns:
            Response (json)                - The JSON data of the action
        '''
        if action_id is None:
            action_id = self._get_last_run_action_id()

        filters = []
        filters.append('action_run="{}"'.format(action_run_id))
        post_response = self._sess.get(self._url("app_run", filters=filters))
        if wait:
            return self._wait(url, interval, max_attempts)
        else:
            return post_response.json()


    """
    Actions: Setting and Getting Variables
    """
    def _set_last_run_product_name(self, product_name):
        self._last_run_product_name = product_name

    def _get_last_run_product_name(self):
        return self._last_run_product_name

    def _set_last_run_application_id(self, application_id):
        self._last_run_application_id = application_id

    def _get_last_run_application_id(self):
        return self._last_run_application_id

    def _set_last_run_action_id(self, action_id):
        self._last_run_action_id = action_id

    def _get_last_run_action_id(self):
        return self._last_run_action_id

    def _set_last_run_action_name(self, action_name):
        self._last_run_action_name = action_name

    def _get_last_run_action_name(self):
        return self._last_run_action_name

    """
    Actions: Properties
    """
    last_run_product_name = property(_get_last_run_product_name, _set_last_run_product_name)
    last_run_application_id = property(_get_last_run_application_id, _set_last_run_application_id)
    last_run_action_name = property(_get_last_run_action_name, _set_last_run_action_name)
    last_run_action_id = property(_get_last_run_action_id, _set_last_run_action_id)

    """
    Miscellanous: Functions
    """
    def get_jira_ticket_data(self, container_id=None, jira_ticket):
        '''
        Function: get_jira_ticket_data

        Description:
        Executes a run_action for the JIRA asset, using the 'get ticket' action, to return all the metadata regarding a JIRA ticket.

        Args:
            jira_ticket (str)               - The JIRA ticket number to retrieve all the metadata for.
            (optional) container_id (str)   - The container ID to run against, by default will use the current container.

        Returns:
            action_results (json)            - The JSON containing all the metadata of the JIRA ticket
        '''
        if cointainer_id is None:
            container_id = self._get_container_id()
        parameters=[{'id': jira_ticket}]

        self.run_action("get ticket", "jira", parameters)
        self.get_action_results()
        action_results = self.get_action_run_data()
        return action_results
