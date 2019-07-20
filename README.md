# Phantasm
Phantasm is a library that has been developed for programmatic testing of Splunk Phantom playbooks. In doing so allowing for test-driven development as users develop playbooks. 

It relies on the Django based REST API in Splunk Phantom to create containers, artifacts, upload files, run playbooks, run individual app actions, promote/demote a case to a container, delete a container and more. It returns the JSON response from each action, allowing the fields to be used in pytest.

Refer to _demo.py_ to showcase the basic functionality of the library, or _test_example.py_ file for a basic example that uses pytest to validate.

## Configuration
Ensure you provide a valid `ph-auth-token` and `phantom-url` in the config.ini file.

## Supported Functions
Each function is documented for further information:
```python
    # Get information relating to the object, including classes
    print('{}').format(phantasm.__doc__)
    print(help(phantasm))

    # Get information relating to an individual function
    print('{}').format(phantasm.create_container.__doc__)
    print(help(phantasm.create_container))
```

### Container Functions:
 - **create_container** - Creates a new container
 - **update_container_status** - Updates the container status
 - **update_container_tags** - Adds a tag to the container
 - **get_container_artifacts** - Retrieves the list of artifacts currently in the container
 - **promote_container_to_case** - Promotes the current container to a case
 - **demote_case_to_container** - Demotes the current case to a container
 - **delete_container** - Deletes a container

### Artifact Functions:
 - **add_artifact** - Adds an artifact to a container
 - **upload_file_to_phantom** - Uploads a file to a container

### Playbook Functions:
 - **run_playbook** - Runs a playbook against a container
 - **get_playbook_results** - Retrieves the status of the playbook
 - **get_playbook_action_results** - Retrieves the status of the last run action in the playbook
 - **get_application_id** - Retrieves an application id
 - **run_action** - Run an individual apps action (i.e: App: SMTP Action: `'test connectivity'`)
 - **get_action_results** - Retrieve the results of an action
 - **get_action_run_data** - Retrieve the data of the action
 - **get_jira_ticket_data** - Runs an action to retrieve all JIRA tickets.

### Changelog:
 - **2019-07-21**: Initial Git Commit (untested)
