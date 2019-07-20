"""
File: demo.py

Description:
    Showcases how to use use the phantasm class, including the various
    functions and variables.

    This is purely meant for demonstration purposes.
"""
import os, sys, csv
import json
import requests
import random
import phantasm

def demo():
    # Get information relating to the object, including classes
    print('{}').format(phantasm.__doc__)
    print(help(phantasm))

    # Get information relating to an individual function
    print('{}').format(phantasm.create_container.__doc__)
    print(help(phantasm.create_container))

    # Create an instance of the Phantasm class
    ph = phantasm.phantasm()

    # Create a new Container
    name = 'Testing: Sample Container Name'
    label = 'Splunk'
    new_container = ph.create_container(name, label)
    print('Container {} was created with ID: {}').format(ph.container_name, ph.container_id)
    print('More Detailed Analysis:\n{}').format(json.dumps(new_container), sort_keys=True, indent=4))

    # Lets transition to the next stage from open
    status = "Open"
    ph.update_container_status(status)

    # Once you've created a container you can check the help again using the following
    print(ph)

    # Add artifacts to the container. Can add multiple artifacts by calling the same method again.
    # Alternatively can add an artifact by providing the information when you create the container.
    cef = {
        'jira_comment': 'This is the comment that would appear in the JIRA ticket',
        'jira_case': 'JIRA-0001',
        'jira_summary': 'TEST_IGNORE: Demonstrating an Artifact',
        'jira_issue_type': 'Malware'
    }
    name = 'Demonstration Artifact'
    description = 'This is a demonstration artifact'
    label = 'event'
    new_artifact = ph.add_artifact(cef, name, description, label)
    print('Artifact {} was created with ID: {}').format(ph.artifact_name, ph.artifact_id)
    print('More Detailed Analysis:\n {}').format(json.dumps(new_artifact), sort_keys=True, indent=4)

    # Adds a file to a container
    file_name = 'path/to/file.txt'
    vault_file = ph.upload_file_to_phantom(file_name)
    print('File {} was added with ID: {}').format(ph.file_name, ph.file_id)
    print('More Detailed Analysis:\n {}').format(json.dumps(vault_file), sort_keys=True, indent=4)

    # Runs a playbook, scope defaults to new, and won't execute without run_confirmation set to true
    playbook_name = 'phantom-playbook/Create JIRA Ticket'
    scope = 'new'
    playbook_results = ph.run_playbook(playbook_name, scope)
    print('Playbook {} with ID {} has commenced running').format(ph.playbook_name, ph.playbook_id)
    print('More Detailed Analysis:\n {}').format(json.dumps(playbook_results), sort_keys=True, indent=4)

    # Get the status of the playbook. Can provide a playbook_id to check.
    print(ph.get_playbook_results())

    # Get the status of the last action that was run by the last run playbook. Can provide a playbook_id to run.
    print(ph.get_playbook_action_results())

    # Run an action, in this case using the JIRA App to list all tickets that match the JQL query
    action_name = 'list tickets'
    asset_name = 'jira'
    parameters = [{
            'project_key': 'JIRA',
            'query': 'summary ~ test12345'
    }]
    action_results = ph.run_action(action_name, asset_name, parameters)
    print('Action {}, with ID {} has commenced running. This uses Product {} with Application ID {}').format(ph.last_run_action_name, ph.last_run_action_id, ph.last_run_product_name, ph.last_run_application_id)

    # Retrieving the action results
    print(ph.get_action_results())

    # Retrieving action run data
    print(ph.get_action_run_data())

    # Retrieve jira tickets properties. If you run ph.retrieve_action_run_data after this you will get activity related to this.
    jira_ticket = 'JIRA-0001'
    print(ph.retrieve_jira_tickets(jira_ticket))

    # Promote container to a case
    template_id = 'Example Template'
    ph.promote_container_to_case(template_id)
    print('Template {} with ID {} has been promoted to Case {}').format(ph.template_name, ph.template_id, ph.case_id)

    # Demote container from a case
    ph.demote_case_to_container()
    print('Template {} with ID {} has been promoted to Case {}').format(ph.template_name, ph.template_id, ph.case_id)

    # Testing has finished, so lets add a tag to Indicate
    tags = []
    tags.append("Completed")
    ph.update_container_tags(tags)

    # Now we can resolve the case
    ph.update_container_status()

    # Delete container, this may have unforeseen consequences. There are two ways.
    userid = 'test'
    password = 'hunter2'
    deleted_container = ph.delete_container(userid, password)
    print('Container {} with ID {} has been removed, detailed analysis: {}').format(ph.container_name, ph.container_id, json.dumps(deleted_container), sort_keys=True, indent=4)


if __name__ == "__main__":
    demo()
