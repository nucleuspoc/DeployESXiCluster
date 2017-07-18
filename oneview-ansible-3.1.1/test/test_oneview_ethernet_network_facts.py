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

from oneview_ethernet_network_facts import EthernetNetworkFactsModule
from test.utils import ModuleContructorTestCase
from test.utils import FactsParamsTestCase
from test.utils import ErrorHandlingTestCase

ERROR_MSG = 'Fake message error'

PARAMS_GET_ALL = dict(
    config='config.json',
    name=None
)

PARAMS_GET_BY_NAME = dict(
    config='config.json',
    name="Test Ethernet Network",
    options=[]
)

PARAMS_GET_BY_NAME_WITH_OPTIONS = dict(
    config='config.json',
    name="Test Ethernet Network",
    options=['associatedProfiles', 'associatedUplinkGroups']
)

PRESENT_ENETS = [{
    "name": "Test Ethernet Network",
    "uri": "/rest/ethernet-networks/d34dcf5e-0d8e-441c-b00d-e1dd6a067188"
}]

ENET_ASSOCIATED_UPLINK_GROUP_URIS = [
    "/rest/uplink-sets/c6bf9af9-48e7-4236-b08a-77684dc258a5",
    "/rest/uplink-sets/e2f0031b-52bd-4223-9ac1-d91cb519d548"
]

ENET_ASSOCIATED_PROFILE_URIS = [
    "/rest/server-profiles/83e2e117-59dc-4e33-9f24-462af951cbbe",
    "/rest/server-profiles/57d3af2a-b6d2-4446-8645-f38dd808ea4d"
]

ENET_ASSOCIATED_UPLINK_GROUPS = [dict(uri=ENET_ASSOCIATED_UPLINK_GROUP_URIS[0], name='Uplink Set 1'),
                                 dict(uri=ENET_ASSOCIATED_UPLINK_GROUP_URIS[1], name='Uplink Set 2')]

ENET_ASSOCIATED_PROFILES = [dict(uri=ENET_ASSOCIATED_PROFILE_URIS[0], name='Server Profile 1'),
                            dict(uri=ENET_ASSOCIATED_PROFILE_URIS[1], name='Server Profile 2')]


class EthernetNetworkFactsSpec(unittest.TestCase,
                               ModuleContructorTestCase,
                               FactsParamsTestCase,
                               ErrorHandlingTestCase):
    def setUp(self):
        self.configure_mocks(self, EthernetNetworkFactsModule)
        self.ethernet_networks = self.mock_ov_client.ethernet_networks
        FactsParamsTestCase.configure_client_mock(self, self.ethernet_networks)
        ErrorHandlingTestCase.configure(self, method_to_fire=self.ethernet_networks.get_by)

    def test_should_get_all_enets(self):
        self.ethernet_networks.get_all.return_value = PRESENT_ENETS
        self.mock_ansible_module.params = PARAMS_GET_ALL

        EthernetNetworkFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(ethernet_networks=(PRESENT_ENETS))
        )

    def test_should_get_enet_by_name(self):
        self.ethernet_networks.get_by.return_value = PRESENT_ENETS
        self.mock_ansible_module.params = PARAMS_GET_BY_NAME

        EthernetNetworkFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(ethernet_networks=(PRESENT_ENETS))
        )

    def test_should_get_enet_by_name_with_options(self):
        self.ethernet_networks.get_by.return_value = PRESENT_ENETS
        self.ethernet_networks.get_associated_profiles.return_value = ENET_ASSOCIATED_PROFILE_URIS
        self.ethernet_networks.get_associated_uplink_groups.return_value = ENET_ASSOCIATED_UPLINK_GROUP_URIS
        self.mock_ov_client.server_profiles.get.side_effect = ENET_ASSOCIATED_PROFILES
        self.mock_ov_client.uplink_sets.get.side_effect = ENET_ASSOCIATED_UPLINK_GROUPS

        self.mock_ansible_module.params = PARAMS_GET_BY_NAME_WITH_OPTIONS

        EthernetNetworkFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(ethernet_networks=PRESENT_ENETS,
                               enet_associated_profiles=ENET_ASSOCIATED_PROFILES,
                               enet_associated_uplink_groups=ENET_ASSOCIATED_UPLINK_GROUPS)
        )


if __name__ == '__main__':
    unittest.main()
