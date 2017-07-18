# -*- coding: utf-8 -*-
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

from test.utils import PreloadedMocksBaseTestCase, ModuleContructorTestCase, ErrorHandlingTestCase
from oneview_logical_enclosure import LogicalEnclosureModule, LOGICAL_ENCLOSURE_UPDATED, \
    LOGICAL_ENCLOSURE_ALREADY_UPDATED, LOGICAL_ENCLOSURE_FIRMWARE_UPDATED, \
    LOGICAL_ENCLOSURE_CONFIGURATION_SCRIPT_UPDATED, \
    LOGICAL_ENCLOSURE_DUMP_GENERATED, LOGICAL_ENCLOSURE_RECONFIGURED, LOGICAL_ENCLOSURE_UPDATED_FROM_GROUP, \
    LOGICAL_ENCLOSURE_REQUIRED, LOGICAL_ENCLOSURE_CREATED, LOGICAL_ENCLOSURE_DELETED, LOGICAL_ENCLOSURE_ALREADY_ABSENT

YAML_LOGICAL_ENCLOSURE = """
    config: "{{ config }}"
    state: present
    data:
        uri: /rest/logical-enclosures/4671582d-1746-4122-9cf0-642a59543509
        name: "Encl1"
    """

YAML_LOGICAL_ENCLOSURE_PRESENT = """
        config: "{{ config }}"
        state: present
        data:
            name: "Encl1"
            enclosureGroupUri: /rest/enclosure-groups/d59d2362-c1b8-44c2-93a0-115229b0c94b
            enclosureUris:
                - /rest/enclosures/0000000000A66101
        """

YAML_LOGICAL_ENCLOSURE_FIRMWARE_UPDATE = """
        config: "{{ config }}"
        state: firmware_updated
        data:
            name: "Encl1"
            firmware:
                firmwareBaselineUri: "/rest/firmware-drivers/SPPGen9Snap3_2015_0221_71"
                firmwareUpdateOn: "EnclosureOnly"
                forceInstallFirmware: "false"
      """

YAML_LOGICAL_ENCLOSURE_UPDATE_SCRIPT = """
        config: "{{ config }}"
        state: script_updated
        data:
            name: "Encl1"
            configurationScript: "# script (updated)"
      """

YAML_LOGICAL_ENCLOSURE_DUMP = """
        config: "{{ config }}"
        state: dumped
        data:
            name: "Encl1"
            dump:
              errorCode: "MyDump16"
              encrypt: "true"
              excludeApplianceDump: "false"
        """

YAML_LOGICAL_ENCLOSURE_CONFIGURE = """
        config: "{{ config }}"
        state: reconfigured
        data:
            name: "Encl1"
    """

YAML_LOGICAL_ENCLOSURE_UPDATE_FROM_GROUP = """
        config: "{{ config }}"
        state: updated_from_group
        data:
            name: "Encl1"
    """

YAML_LOGICAL_ENCLOSURE_RENAME = """
        config: "{{ config }}"
        state: present
        data:
            name: "Encl1"
            newName: "Encl1 (renamed)"
        """

YAML_LOGICAL_ENCLOSURE_NO_RENAME = """
    config: "{{ config }}"
    state: present
    data:
        name: "Encl1 (renamed)"
        newName: "Encl1"
    """

YAML_LOGICAL_ENCLOSURE_ABSENT = """
        config: "{{ config }}"
        state: absent
        data:
            name: "Encl1"
        """

DICT_DEFAULT_LOGICAL_ENCLOSURE = yaml.load(YAML_LOGICAL_ENCLOSURE)["data"]


class LogicalEnclosureModuleSpec(unittest.TestCase,
                                 ModuleContructorTestCase,
                                 ErrorHandlingTestCase):
    """
    Test the module constructor
    ModuleContructorTestCase has common tests for class constructor and main function

    ErrorHandlingTestCase has common tests for the module error handling.
    """
    def setUp(self):
        self.configure_mocks(self, LogicalEnclosureModule)
        ErrorHandlingTestCase.configure(self, method_to_fire=self.mock_ov_client.logical_enclosures.get_by_name)


class LogicalEnclosureSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    def setUp(self):
        self.configure_mocks(self, LogicalEnclosureModule)

    def test_should_create_when_resource_not_exist(self):
        self.mock_ov_client.logical_enclosures.get_by_name.return_value = None
        self.mock_ov_client.logical_enclosures.create.return_value = DICT_DEFAULT_LOGICAL_ENCLOSURE
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_PRESENT)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=LOGICAL_ENCLOSURE_CREATED,
            ansible_facts=dict(logical_enclosure=DICT_DEFAULT_LOGICAL_ENCLOSURE)
        )

    def test_should_not_update_when_existing_data_is_equals(self):
        self.mock_ov_client.logical_enclosures.get_by_name.return_value = DICT_DEFAULT_LOGICAL_ENCLOSURE
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_NO_RENAME)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=LOGICAL_ENCLOSURE_ALREADY_UPDATED,
            ansible_facts=dict(logical_enclosure=DICT_DEFAULT_LOGICAL_ENCLOSURE)
        )

    def test_should_update_when_data_has_modified_attributes(self):
        data_merged = DICT_DEFAULT_LOGICAL_ENCLOSURE.copy()
        data_merged['newName'] = 'New Name'

        self.mock_ov_client.logical_enclosures.get_by_name.return_value = DICT_DEFAULT_LOGICAL_ENCLOSURE
        self.mock_ov_client.logical_enclosures.update.return_value = data_merged
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_RENAME)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=LOGICAL_ENCLOSURE_UPDATED,
            ansible_facts=dict(logical_enclosure=data_merged)
        )

    def test_should_update_firmware_when_resource_exists(self):
        self.mock_ov_client.logical_enclosures.get_by_name.return_value = DICT_DEFAULT_LOGICAL_ENCLOSURE
        self.mock_ov_client.logical_enclosures.patch.return_value = {'PATCH', 'EXECUTED'}
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_FIRMWARE_UPDATE)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=LOGICAL_ENCLOSURE_FIRMWARE_UPDATED,
            ansible_facts=dict(logical_enclosure={'PATCH', 'EXECUTED'})
        )

    def test_should_not_update_firmware_when_resource_not_found(self):
        self.mock_ov_client.logical_enclosures.get_by_name.return_value = None
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_FIRMWARE_UPDATE)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=LOGICAL_ENCLOSURE_REQUIRED)

    def test_should_update_script_when_resource_exists(self):
        self.mock_ov_client.logical_enclosures.get_by_name.return_value = DICT_DEFAULT_LOGICAL_ENCLOSURE
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_UPDATE_SCRIPT)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=LOGICAL_ENCLOSURE_CONFIGURATION_SCRIPT_UPDATED,
            ansible_facts=dict(configuration_script='# script (updated)')
        )

    def test_should_not_update_script_when_resource_not_found(self):
        self.mock_ov_client.logical_enclosures.get_by_name.return_value = None
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_UPDATE_SCRIPT)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=LOGICAL_ENCLOSURE_REQUIRED)

    def test_should_generate_support_dump_when_resource_exist(self):
        self.mock_ov_client.logical_enclosures.get_by_name.return_value = DICT_DEFAULT_LOGICAL_ENCLOSURE
        self.mock_ov_client.logical_enclosures.generate_support_dump.return_value = '/rest/appliance/dumpedfile'
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_DUMP)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=LOGICAL_ENCLOSURE_DUMP_GENERATED,
            ansible_facts=dict(generated_dump_uri='/rest/appliance/dumpedfile')
        )

    def test_should_not_generate_support_dump_when_resource_not_found(self):
        self.mock_ov_client.logical_enclosures.get_by_name.return_value = None
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_DUMP)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=LOGICAL_ENCLOSURE_REQUIRED)

    def test_should_reconfigure_when_resource_exist(self):
        self.mock_ov_client.logical_enclosures.get_by_name.return_value = DICT_DEFAULT_LOGICAL_ENCLOSURE
        self.mock_ov_client.logical_enclosures.update_configuration.return_value = {'Configuration', 'Updated'}
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_CONFIGURE)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=LOGICAL_ENCLOSURE_RECONFIGURED,
            ansible_facts=dict(logical_enclosure={'Configuration', 'Updated'})
        )

    def test_should_not_reconfigure_when_resource_not_found(self):
        self.mock_ov_client.logical_enclosures.get_by_name.return_value = None
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_CONFIGURE)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=LOGICAL_ENCLOSURE_REQUIRED)

    def test_should_update_from_group_when_resource_exist(self):
        self.mock_ov_client.logical_enclosures.get_by_name.return_value = DICT_DEFAULT_LOGICAL_ENCLOSURE
        self.mock_ov_client.logical_enclosures.update_from_group.return_value = {'Updated from group'}
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_UPDATE_FROM_GROUP)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=LOGICAL_ENCLOSURE_UPDATED_FROM_GROUP,
            ansible_facts=dict(logical_enclosure={'Updated from group'})
        )

    def test_should_not_update_from_group_when_resource_not_found(self):
        self.mock_ov_client.logical_enclosures.get_by_name.return_value = None
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_UPDATE_FROM_GROUP)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=LOGICAL_ENCLOSURE_REQUIRED)

    def test_should_delete_logical_enclosure_when_resource_exist(self):
        self.mock_ov_client.logical_enclosures.get_by_name.return_value = DICT_DEFAULT_LOGICAL_ENCLOSURE
        self.mock_ov_client.logical_enclosures.delete.return_value = True
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_ABSENT)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=LOGICAL_ENCLOSURE_DELETED,
            ansible_facts=dict(logical_enclosure=None)
        )

    def test_should_do_nothing_when_resource_already_absent(self):
        self.mock_ov_client.logical_enclosures.get_by_name.return_value = None
        self.mock_ansible_module.params = yaml.load(YAML_LOGICAL_ENCLOSURE_ABSENT)

        LogicalEnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=LOGICAL_ENCLOSURE_ALREADY_ABSENT,
            ansible_facts=dict(logical_enclosure=None)
        )


if __name__ == '__main__':
    unittest.main()
