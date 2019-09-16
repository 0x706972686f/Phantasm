"""
File: test_example.py

Description:
    A very simple test case for creating a JIRA ticket. It completes the following
    actions:
    
    1) Creates a pytest fixture that is an instance of the class.
    2) It creates a container
    3) It adds two artifacts to the container, which will be the JIRA ticket information
    4) It runs a playbook 'Create JIRA ticket' which will create a JIRA ticket based
       on the artifacts
    5) Finally it verifies the playbook ran by checking the playbook run data to 
       confirm the JSON response from JIRA, looking for the field that shows the
       tickets are open.
"""

import os
import sys
import csv
import json
import pytest
import phantasm

'''Create an instance of Phantasm'''
@pytest.fixture
def phantasm_instance():
    return phantasm.phantasm()

'''Creating a Container'''
@pytest.mark.parametrize("containername,label", [
  ("container-test1", "test"),
])
@pytest.mark.first
def test_create_container(phantasm_instance, containername, label):
    assert phantasm_instance.create_container(containername, label).get("id") is not None

'''Adding two artifacts to the container'''
@pytest.mark.parametrize("cef,artifactname,description,label", [
    ({
        'jira_comment': 'This is the comment that would appear in the JIRA ticket',
        'jira_case': 'JIRA-0001',
        'jira_summary': 'TEST_IGNORE: Demonstrating an Artifact',
        'jira_issue_type': 'Malware'
    },
    "artifact1","This is a test Artifact","test"),
     ({
        'jira_comment': 'This is the comment that would appear in the JIRA ticket',
        'jira_case': 'JIRA-0001',
        'jira_summary': 'TEST_IGNORE: Demonstrating an Artifact',
        'jira_issue_type': 'Malware'
    },
    "artifact2","This is a test Artifact","test"),
])
@pytest.mark.second
def test_add_artifact(phantasm_instance, cef, artifactname, description, label):
    assert phantasm_instance.add_artifact(cef, artifactname, description, label).get("id") is not None

'''Run a playbook'''
@pytest.mark.parametrize("playbook_name,scope", [
    ("phantom-playbook/Create JIRA Ticket","new"),
])
def test_run_playbook(phantasm_instance, playbook_name, scope):
    assert phantasm_instance.run_playbook(playbook_name, scope).get("status") == "success"

'''Get the Detailed JSON for conclusive testing'''
@pytest.mark.last
def test_playbook_run_data(phantasm_instance):
    detailed_outcome = phantasm_instance.get_playbook_run_data()
    assert detailed_outcome['data'][0]['result_data'][0]['data'][0]['status'] == 'open'
