# Phantasm
A test automation framework built for Splunk Phantom Playbooks. Allows for programatically testing and validating playbooks.

Phantasm is a library that has been developed for programmatic testing of Splunk Phantom. In doing so we can use test-driven development to test playbooks

The class will allow you to create containers and artifacts, as well as allow you to run playbooks, individual actions, upload files to the vault, promote or demote a container to a case, delete a container, and retrieve the JSON data relating to all the actions.

Refer to _demo.py_ to showcase the basic functionality of the library, or _test_example.py_ file for a basic example that uses pytest to validate.

The code is documented for further information:
```python
    # Get information relating to the object, including classes
    print('{}').format(phantasm.__doc__)
    print(help(phantasm))

    # Get information relating to an individual function
    print('{}').format(phantasm.create_container.__doc__)
    print(help(phantasm.create_container))
```

### Changelog:
 - **2019-07-21**: Initial Git Commit (untested)
