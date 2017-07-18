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

from oneview_ethernet_network import EthernetNetworkModule, ETHERNET_NETWORK_CREATED, ETHERNET_NETWORK_ALREADY_EXIST, \
    ETHERNET_NETWORK_UPDATED, ETHERNET_NETWORK_DELETED, ETHERNET_NETWORK_ALREADY_ABSENT, \
    ETHERNET_NETWORKS_CREATED, MISSING_ETHERNET_NETWORKS_CREATED, ETHERNET_NETWORKS_ALREADY_EXIST, \
    ETHERNET_NETWORK_CONNECTION_TEMPLATE_RESET, ETHERNET_NETWORK_NOT_FOUND
from test.utils import ModuleContructorTestCase
from test.utils import ValidateEtagTestCase
from test.utils import ErrorHandlingTestCase

FAKE_MSG_ERROR = 'Fake message error'
DEFAULT_ETHERNET_NAME = 'Test Ethernet Network'
RENAMED_ETHERNET = 'Renamed Ethernet Network'

DEFAULT_ENET_TEMPLATE = dict(
    name=DEFAULT_ETHERNET_NAME,
    vlanId=200,
    ethernetNetworkType="Tagged",
    purpose="General",
    smartLink=False,
    privateNetwork=False,
    connectionTemplateUri=None
)

PARAMS_FOR_PRESENT = dict(
    config='config.json',
    state='present',
    data=dict(name=DEFAULT_ETHERNET_NAME)
)

PARAMS_TO_RENAME = dict(
    config='config.json',
    state='present',
    data=dict(name=DEFAULT_ETHERNET_NAME,
              newName=RENAMED_ETHERNET)
)

YAML_PARAMS_WITH_CHANGES = """
    config: "config.json"
    state: present
    data:
      name: 'Test Ethernet Network'
      purpose: Management
      connectionTemplateUri: ~
      bandwidth:
          maximumBandwidth: 3000
          typicalBandwidth: 2000
"""

YAML_RESET_CONNECTION_TEMPLATE = """
        config: "{{ config }}"
        state: default_bandwidth_reset
        data:
          name: 'network name'
"""

PARAMS_FOR_ABSENT = dict(
    config='config.json',
    state='absent',
    data=dict(name=DEFAULT_ETHERNET_NAME)
)

PARAMS_FOR_BULK_CREATED = dict(
    config='config.json',
    state='present',
    data=dict(namePrefix="TestNetwork", vlanIdRange="1-2,5,9-10")
)

DEFAULT_BULK_ENET_TEMPLATE = [
    {'name': 'TestNetwork_1', 'vlanId': 1},
    {'name': 'TestNetwork_2', 'vlanId': 2},
    {'name': 'TestNetwork_5', 'vlanId': 5},
    {'name': 'TestNetwork_9', 'vlanId': 9},
    {'name': 'TestNetwork_10', 'vlanId': 10},
]

DICT_PARAMS_WITH_CHANGES = yaml.load(YAML_PARAMS_WITH_CHANGES)["data"]


class EthernetNetworkModuleSpec(unittest.TestCase,
                                ModuleContructorTestCase,
                                ValidateEtagTestCase,
                                ErrorHandlingTestCase):
    """
    ModuleContructorTestCase has common tests for class constructor and main function,
    also provides the mocks used in this test case

    ValidateEtagTestCase has common tests for the validate_etag attribute.

    ErrorHandlingTestCase has common tests for the module error handling.
    """

    def setUp(self):
        self.configure_mocks(self, EthernetNetworkModule)
        self.resource = self.mock_ov_client.ethernet_networks
        ErrorHandlingTestCase.configure(self, ansible_params=PARAMS_TO_RENAME, method_to_fire=self.resource.get_by)

    def test_should_create_new_ethernet_network(self):
        self.resource.get_by.return_value = []
        self.resource.create.return_value = DEFAULT_ENET_TEMPLATE

        self.mock_ansible_module.params = PARAMS_FOR_PRESENT

        EthernetNetworkModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ETHERNET_NETWORK_CREATED,
            ansible_facts=dict(ethernet_network=DEFAULT_ENET_TEMPLATE)
        )

    def test_should_not_update_when_data_is_equals(self):
        self.resource.get_by.return_value = [DEFAULT_ENET_TEMPLATE]

        self.mock_ansible_module.params = PARAMS_FOR_PRESENT

        EthernetNetworkModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=ETHERNET_NETWORK_ALREADY_EXIST,
            ansible_facts=dict(ethernet_network=DEFAULT_ENET_TEMPLATE)
        )

    def test_update_when_data_has_modified_attributes(self):
        data_merged = DEFAULT_ENET_TEMPLATE.copy()
        data_merged['purpose'] = 'Management'

        self.resource.get_by.return_value = [DEFAULT_ENET_TEMPLATE]
        self.resource.update.return_value = data_merged
        self.mock_ov_client.connection_templates.get.return_value = {"uri": "uri"}

        self.mock_ansible_module.params = yaml.load(YAML_PARAMS_WITH_CHANGES)

        EthernetNetworkModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ETHERNET_NETWORK_UPDATED,
            ansible_facts=dict(ethernet_network=data_merged)
        )

    def test_update_when_only_bandwidth_has_modified_attributes(self):
        self.resource.get_by.return_value = [DICT_PARAMS_WITH_CHANGES]
        self.mock_ov_client.connection_templates.get.return_value = {"uri": "uri"}

        self.mock_ansible_module.params = yaml.load(YAML_PARAMS_WITH_CHANGES)

        EthernetNetworkModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ETHERNET_NETWORK_UPDATED,
            ansible_facts=dict(ethernet_network=DICT_PARAMS_WITH_CHANGES)
        )

    def test_update_when_data_has_modified_attributes_but_bandwidth_is_equal(self):
        data_merged = DEFAULT_ENET_TEMPLATE.copy()
        data_merged['purpose'] = 'Management'

        self.resource.get_by.return_value = [DEFAULT_ENET_TEMPLATE]
        self.resource.update.return_value = data_merged
        self.mock_ov_client.connection_templates.get.return_value = {
            "bandwidth": DICT_PARAMS_WITH_CHANGES['bandwidth']}

        self.mock_ansible_module.params = yaml.load(YAML_PARAMS_WITH_CHANGES)

        EthernetNetworkModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ETHERNET_NETWORK_UPDATED,
            ansible_facts=dict(ethernet_network=data_merged)
        )

    def test_update_successfully_even_when_connection_template_uri_not_exists(self):
        data_merged = DEFAULT_ENET_TEMPLATE.copy()
        del data_merged['connectionTemplateUri']

        self.resource.get_by.return_value = [DEFAULT_ENET_TEMPLATE]
        self.resource.update.return_value = data_merged

        self.mock_ansible_module.params = yaml.load(YAML_PARAMS_WITH_CHANGES)

        EthernetNetworkModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ETHERNET_NETWORK_UPDATED,
            ansible_facts=dict(ethernet_network=data_merged)
        )

    def test_rename_when_resource_exists(self):
        data_merged = DEFAULT_ENET_TEMPLATE.copy()
        data_merged['name'] = RENAMED_ETHERNET
        params_to_rename = PARAMS_TO_RENAME.copy()

        self.resource.get_by.return_value = [DEFAULT_ENET_TEMPLATE]
        self.resource.update.return_value = data_merged

        self.mock_ansible_module.params = params_to_rename

        EthernetNetworkModule().run()

        self.resource.update.assert_called_once_with(data_merged)

    def test_create_with_new_name_when_resource_not_exists(self):
        data_merged = DEFAULT_ENET_TEMPLATE.copy()
        data_merged['name'] = RENAMED_ETHERNET
        params_to_rename = PARAMS_TO_RENAME.copy()

        self.resource.get_by.return_value = []
        self.resource.create.return_value = DEFAULT_ENET_TEMPLATE

        self.mock_ansible_module.params = params_to_rename

        EthernetNetworkModule().run()

        self.resource.create.assert_called_once_with(PARAMS_TO_RENAME['data'])

    def test_should_remove_ethernet_network(self):
        self.resource.get_by.return_value = [DEFAULT_ENET_TEMPLATE]

        self.mock_ansible_module.params = PARAMS_FOR_ABSENT

        EthernetNetworkModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts={},
            msg=ETHERNET_NETWORK_DELETED
        )

    def test_should_do_nothing_when_ethernet_network_not_exist(self):
        self.resource.get_by.return_value = []

        self.mock_ansible_module.params = PARAMS_FOR_ABSENT

        EthernetNetworkModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            ansible_facts={},
            changed=False,
            msg=ETHERNET_NETWORK_ALREADY_ABSENT
        )

    def test_should_create_all_ethernet_networks(self):
        self.resource.get_range.return_value = []
        self.resource.create_bulk.return_value = DEFAULT_BULK_ENET_TEMPLATE

        self.mock_ansible_module.params = PARAMS_FOR_BULK_CREATED

        EthernetNetworkModule().run()

        self.resource.create_bulk.assert_called_once_with(
            dict(namePrefix="TestNetwork", vlanIdRange="1-2,5,9-10"))
        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ETHERNET_NETWORKS_CREATED,
            ansible_facts=dict(ethernet_network_bulk=DEFAULT_BULK_ENET_TEMPLATE))

    def test_should_create_missing_ethernet_networks(self):
        enet_get_range_return = [
            {'name': 'TestNetwork_1', 'vlanId': 1},
            {'name': 'TestNetwork_2', 'vlanId': 2},
        ]

        self.resource.get_range.side_effect = [enet_get_range_return, DEFAULT_BULK_ENET_TEMPLATE]
        self.resource.dissociate_values_or_ranges.return_value = [1, 2, 5, 9, 10]

        self.mock_ansible_module.params = PARAMS_FOR_BULK_CREATED

        EthernetNetworkModule().run()

        self.resource.create_bulk.assert_called_once_with(
            dict(namePrefix="TestNetwork", vlanIdRange="5,9,10"))
        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True, msg=MISSING_ETHERNET_NETWORKS_CREATED,
            ansible_facts=dict(ethernet_network_bulk=DEFAULT_BULK_ENET_TEMPLATE))

    def test_should_create_missing_ethernet_networks_with_just_one_difference(self):
        enet_get_range_return = [
            {'name': 'TestNetwork_1', 'vlanId': 1},
            {'name': 'TestNetwork_2', 'vlanId': 2},
        ]

        self.resource.get_range.side_effect = [enet_get_range_return, DEFAULT_BULK_ENET_TEMPLATE]
        self.resource.dissociate_values_or_ranges.return_value = [1, 2, 5]

        self.mock_ansible_module.params = PARAMS_FOR_BULK_CREATED

        EthernetNetworkModule().run()

        self.resource.create_bulk.assert_called_once_with({'vlanIdRange': '5-5', 'namePrefix': 'TestNetwork'})

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=MISSING_ETHERNET_NETWORKS_CREATED,
            ansible_facts=dict(ethernet_network_bulk=DEFAULT_BULK_ENET_TEMPLATE))

    def test_should_do_nothing_when_ethernet_networks_already_exist(self):
        self.resource.get_range.return_value = DEFAULT_BULK_ENET_TEMPLATE
        self.resource.dissociate_values_or_ranges.return_value = [1, 2, 5, 9, 10]

        self.mock_ansible_module.params = PARAMS_FOR_BULK_CREATED

        EthernetNetworkModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False, msg=ETHERNET_NETWORKS_ALREADY_EXIST,
            ansible_facts=dict(ethernet_network_bulk=DEFAULT_BULK_ENET_TEMPLATE))

    def test_reset_successfully(self):
        self.resource.get_by.return_value = [DICT_PARAMS_WITH_CHANGES]
        self.mock_ov_client.connection_templates.update.return_value = {'result': 'success'}
        self.mock_ov_client.connection_templates.get.return_value = {
            "bandwidth": DICT_PARAMS_WITH_CHANGES['bandwidth']}

        self.mock_ov_client.connection_templates.get_default.return_value = {"bandwidth": {
            "max": 1
        }}

        self.mock_ansible_module.params = yaml.load(YAML_RESET_CONNECTION_TEMPLATE)

        EthernetNetworkModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True, msg=ETHERNET_NETWORK_CONNECTION_TEMPLATE_RESET,
            ansible_facts=dict(ethernet_network_connection_template={'result': 'success'}))

    def test_should_fail_when_reset_not_existing_ethernet_network(self):
        self.resource.get_by.return_value = [None]

        self.mock_ansible_module.params = yaml.load(YAML_RESET_CONNECTION_TEMPLATE)

        EthernetNetworkModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(
            msg=ETHERNET_NETWORK_NOT_FOUND
        )


if __name__ == '__main__':
    unittest.main()
