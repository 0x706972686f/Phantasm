"""
File: test_example.py

Description:
    A very simple test case that creates a container, adds an artifact to that
    container (which is the details for a new JIRA ticket), then runs a playbook
    which ensures that the ticket was closed.
"""

import os, sys, csv
import json
import phantasm

'''Create an instance of Phantasm'''
def create_phantasm():
    ph = phantasm.phantasm()
    return ph

'''Creating a Container'''
def create_container(phantasmobj, name, label):
    try:
        c = phantasmobj.create_container(name, label)
        if c is None:
            raise phantasm.containerException
        else:
            return c
    except phantasm.containerException:
        print("Failed to Create the Container")

'''Adding an artifact to the container'''
def add_artifact(phantasmobj, cef, name, description, label):
    try:
        a = phantasmobj.add_artifact(cef, name, description, label)
        if a is None:
            raise phantasm.artifactException
        else:
            return a
    except phantasm.artifactException:
        print("No Artifact was created")

'''Run a playbook'''
def run_playbook(phantasmobj, playbook_name, scope):
    try:
        p = phantasmobj.run_playbook(playbook_name, scope)
        if p is None:
            raise phantasm.playbookException
        else:
            return a
    except phantasm.playbookException:
        print("The playbook was not executed")

'''The test cases for pytest to validate'''
def test_utils():
    new_phantasm = create_phantasm()

    container_name = 'Testing: PyTest Validating Containers'
    container_label = 'Splunk'

    container = create_container(new_phantasm, container_name, container_label)

    cef = {
        'jira_comment': 'This is the comment that would appear in the JIRA ticket',
        'jira_case': 'JIRA-0001',
        'jira_summary': 'TEST_IGNORE: Demonstrating an Artifact',
        'jira_issue_type': 'Malware'
    }
    name = 'Demonstration Artifact'
    description = 'This is a demonstration artifact'
    label = 'event'

    artifact = add_artifact(new_phantasm, cef, name, description, label)

    playbook_name = 'phantom-playbook/Create JIRA Ticket'
    scope = 'new'

    playbook = run_playbook(new_phantasm, playbook_name, scope)
    detailed_outcome = new_phantasm.get_playbook_run_data()

    #assert new_phantasm.container_id not None
    assert container.get("id") not None
    #assert new_phantasm.artifact_id not None
    assert artifact.get("id") not None
    #assert new_phantasm.get_playbook_results().get("status") is "success"
    assert playbook.get("status") is "success"
    #asset new_phantasm.get_playbook_run_action_status(action="get ticket")['data'][0]['result_data'][0]['data'][0]['status'] is 'closed'
    assert detailed_outcome['data'][0]['result_data'][0]['data'][0]['status'] is 'closed'
