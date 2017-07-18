###
# Copyright (2016) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###
import unittest
import yaml

from oneview_enclosure_group import EnclosureGroupModule, ENCLOSURE_GROUP_CREATED, ENCLOSURE_GROUP_ALREADY_EXIST, \
    ENCLOSURE_GROUP_UPDATED, ENCLOSURE_GROUP_DELETED, ENCLOSURE_GROUP_ALREADY_ABSENT
from test.utils import ModuleContructorTestCase
from test.utils import ErrorHandlingTestCase

FAKE_MSG_ERROR = 'Fake message error'

YAML_ENCLOSURE_GROUP = """
        config: "{{ config }}"
        state: present
        data:
            name: "Enclosure Group 1"
            stackingMode: "Enclosure"
            interconnectBayMappings:
                - interconnectBay: 1
                - interconnectBay: 2
                - interconnectBay: 3
                - interconnectBay: 4
                - interconnectBay: 5
                - interconnectBay: 6
                - interconnectBay: 7
                - interconnectBay: 8
          """

YAML_ENCLOSURE_GROUP_CHANGES = """
    config: "{{ config }}"
    state: present
    data:
        name: "Enclosure Group 1"
        newName: "Enclosure Group 1 (Changed)"
        stackingMode: "Enclosure"
        interconnectBayMappings:
            - interconnectBay: 1
            - interconnectBay: 2
            - interconnectBay: 3
            - interconnectBay: 4
            - interconnectBay: 5
            - interconnectBay: 6
            - interconnectBay: 7
            - interconnectBay: 8
      """

YAML_ENCLOSURE_GROUP_CHANGE_SCRIPT = """
    config: "{{ config }}"
    state: present
    data:
        name: "Enclosure Group 1"
        configurationScript: "# test script "
      """

YAML_ENCLOSURE_GROUP_ABSENT = """
        config: "{{ config }}"
        state: absent
        data:
          name: "Enclosure Group 1 (renamed)"
        """

DICT_DEFAULT_ENCLOSURE_GROUP = yaml.load(YAML_ENCLOSURE_GROUP)["data"]


class EnclosureGroupPresentStateSpec(unittest.TestCase,
                                     ModuleContructorTestCase,
                                     ErrorHandlingTestCase):
    """
    ModuleContructorTestCase has common tests for class constructor and main function,
    also provides the mocks used in this test case

    ErrorHandlingTestCase has common tests for the module error handling.
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureGroupModule)
        self.resource = self.mock_ov_client.enclosure_groups

        ErrorHandlingTestCase.configure(self, method_to_fire=self.mock_ov_client.enclosure_groups.get_by)

    def test_should_create_new_enclosure_group(self):
        self.resource.get_by.return_value = []
        self.resource.create.return_value = {"name": "name"}

        self.mock_ansible_module.params = yaml.load(YAML_ENCLOSURE_GROUP)

        EnclosureGroupModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ENCLOSURE_GROUP_CREATED,
            ansible_facts=dict(enclosure_group={"name": "name"})
        )

    def test_should_not_update_when_data_is_equals(self):
        self.resource.get_by.return_value = [DICT_DEFAULT_ENCLOSURE_GROUP]

        self.mock_ansible_module.params = yaml.load(YAML_ENCLOSURE_GROUP)

        EnclosureGroupModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=ENCLOSURE_GROUP_ALREADY_EXIST,
            ansible_facts=dict(enclosure_group=DICT_DEFAULT_ENCLOSURE_GROUP)
        )

    def test_update_when_data_has_modified_attributes(self):
        data_merged = DICT_DEFAULT_ENCLOSURE_GROUP.copy()
        data_merged['newName'] = 'New Name'

        self.resource.get_by.return_value = [DICT_DEFAULT_ENCLOSURE_GROUP]
        self.resource.update.return_value = data_merged

        self.mock_ansible_module.params = yaml.load(YAML_ENCLOSURE_GROUP_CHANGES)

        EnclosureGroupModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ENCLOSURE_GROUP_UPDATED,
            ansible_facts=dict(enclosure_group=data_merged)
        )

    def test_update_when_script_attribute_was_modified(self):
        data_merged = DICT_DEFAULT_ENCLOSURE_GROUP.copy()
        data_merged['newName'] = 'New Name'
        data_merged['uri'] = '/rest/uri'

        self.resource.get_by.return_value = [data_merged]
        self.resource.update_script.return_value = ""
        self.resource.get_by.get_script = "# test script"

        self.mock_ansible_module.params = yaml.load(YAML_ENCLOSURE_GROUP_CHANGE_SCRIPT)

        EnclosureGroupModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ENCLOSURE_GROUP_UPDATED,
            ansible_facts=dict(enclosure_group=data_merged)
        )

    def test_update_when_script_attribute_was_not_modified(self):
        data_merged = DICT_DEFAULT_ENCLOSURE_GROUP.copy()
        data_merged['newName'] = 'New Name'
        data_merged['uri'] = '/rest/uri'

        self.resource.get_by.return_value = [data_merged]
        self.resource.update_script.return_value = ""
        self.resource.get_script.return_value = "# test script "

        self.mock_ansible_module.params = yaml.load(YAML_ENCLOSURE_GROUP_CHANGE_SCRIPT)

        EnclosureGroupModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=ENCLOSURE_GROUP_ALREADY_EXIST,
            ansible_facts=dict(enclosure_group=data_merged)
        )

    def test_should_remove_enclosure_group(self):
        self.resource.get_by.return_value = [DICT_DEFAULT_ENCLOSURE_GROUP]

        self.mock_ansible_module.params = yaml.load(YAML_ENCLOSURE_GROUP_ABSENT)

        EnclosureGroupModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ENCLOSURE_GROUP_DELETED
        )

    def test_should_do_nothing_when_enclosure_group_not_exist(self):
        self.resource.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(YAML_ENCLOSURE_GROUP_ABSENT)

        EnclosureGroupModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=ENCLOSURE_GROUP_ALREADY_ABSENT
        )


if __name__ == '__main__':
    unittest.main()
