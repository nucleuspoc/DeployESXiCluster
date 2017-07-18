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

from oneview_interconnect_facts import InterconnectFactsModule
from oneview_interconnect_facts import EXAMPLES
from test.utils import FactsParamsTestCase
from test.utils import ModuleContructorTestCase
from test.utils import ErrorHandlingTestCase
import yaml

ERROR_MSG = 'Fake message error'

INTERCONNECT_NAME = "0000A66102, interconnect 2"

PARAMS_FOR_GET_ALL = dict(
    config='config.json',
    name=None,
)

PARAMS_FOR_GET_BY_NAME = dict(
    config='config.json',
    name=INTERCONNECT_NAME
)

PARAMS_FOR_GET_NAME_SERVERS = dict(
    config='config.json',
    name=INTERCONNECT_NAME,
    options=['nameServers']
)

INTERCONNECT_URI = "/rest/interconnects/53fa7d35-1cc8-46c1-abf0-6af091a1aed3"
PORT_NAME = "d1"
SUBPORT_NUMBER = 1

PARAMS = dict(
    config='config.json',
    name=INTERCONNECT_NAME,
    options=['statistics']
)

PARAMS_FOR_PORT_STATISTICS = dict(
    config='config.json',
    name=INTERCONNECT_NAME,
    options=[{'portStatistics': PORT_NAME}]
)

PARAMS_FOR_SUBPORT_STATISTICS = dict(
    config='config.json',
    name=INTERCONNECT_NAME,
    options=[{'subPortStatistics': {'portName': PORT_NAME, 'subportNumber': SUBPORT_NUMBER}}]
)

MOCK_INTERCONNECTS = [
    dict(uidState='On', uri=INTERCONNECT_URI)
]


class InterconnectFactsSpec(unittest.TestCase,
                            ModuleContructorTestCase,
                            FactsParamsTestCase,
                            ErrorHandlingTestCase):
    def setUp(self):
        self.configure_mocks(self, InterconnectFactsModule)
        self.interconnects = self.mock_ov_client.interconnects
        FactsParamsTestCase.configure_client_mock(self, self.interconnects)
        ErrorHandlingTestCase.configure(self, method_to_fire=self.interconnects.get_by)

        self.EXAMPLES = yaml.load(EXAMPLES)
        self.PARAMS_GET_ALL_PORTS = self.EXAMPLES[18]['oneview_interconnect_facts']
        self.PARAMS_GET_PORT = self.EXAMPLES[21]['oneview_interconnect_facts']

    def test_should_get_all_interconnects(self):
        fake_interconnects = [dict(uidState='On', name=INTERCONNECT_NAME)]
        self.interconnects.get_all.return_value = fake_interconnects

        self.mock_ansible_module.params = PARAMS_FOR_GET_ALL

        InterconnectFactsModule().run()

        self.interconnects.get_all.assert_called_once()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(interconnects=fake_interconnects)
        )

    def test_should_get_interconnects_by_interconnect_name(self):
        self.interconnects.get_by.return_value = MOCK_INTERCONNECTS

        self.mock_ansible_module.params = PARAMS_FOR_GET_BY_NAME

        InterconnectFactsModule().run()

        self.interconnects.get_by.assert_called_once_with('name', INTERCONNECT_NAME)

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(interconnects=MOCK_INTERCONNECTS)
        )

    def test_should_get_interconnect_name_servers(self):
        fake_name_servers = [dict(t=1)]

        self.interconnects.get_by.return_value = MOCK_INTERCONNECTS
        self.interconnects.get_name_servers.return_value = fake_name_servers

        self.mock_ansible_module.params = PARAMS_FOR_GET_NAME_SERVERS

        InterconnectFactsModule().run()

        self.interconnects.get_by.assert_called_once_with('name', INTERCONNECT_NAME)
        self.interconnects.get_name_servers.assert_called_once_with(INTERCONNECT_URI)

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(interconnects=MOCK_INTERCONNECTS, interconnect_name_servers=fake_name_servers)
        )

    def test_should_get_interconnect_statistics_by_interconnect_name(self):
        self.interconnects.get_by.return_value = MOCK_INTERCONNECTS

        fake_statistics = dict()
        self.interconnects.get_statistics.return_value = fake_statistics

        self.mock_ansible_module.params = PARAMS

        InterconnectFactsModule().run()

        self.interconnects.get_statistics.assert_called_once_with(INTERCONNECT_URI)

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(
                interconnects=MOCK_INTERCONNECTS,
                interconnect_statistics=fake_statistics,

            )
        )

    def test_should_gather_facts_about_interconnect_port_statistics(self):
        fake_statistics = dict(name='test')

        self.interconnects.get_by.return_value = MOCK_INTERCONNECTS
        self.interconnects.get_statistics.return_value = fake_statistics

        self.mock_ansible_module.params = PARAMS_FOR_PORT_STATISTICS

        InterconnectFactsModule().run()

        self.interconnects.get_statistics.assert_called_once_with(INTERCONNECT_URI, PORT_NAME)

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(
                interconnects=MOCK_INTERCONNECTS,
                interconnect_port_statistics=fake_statistics,
            )
        )

    def test_should_gather_facts_about_interconnect_subport_statistics(self):
        fake_statistics = dict(name='test')

        self.interconnects.get_by.return_value = MOCK_INTERCONNECTS
        self.interconnects.get_subport_statistics.return_value = fake_statistics

        self.mock_ansible_module.params = PARAMS_FOR_SUBPORT_STATISTICS

        InterconnectFactsModule().run()

        self.interconnects.get_subport_statistics.assert_called_once_with(
            INTERCONNECT_URI,
            PORT_NAME,
            SUBPORT_NUMBER
        )

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(
                interconnects=MOCK_INTERCONNECTS,
                interconnect_subport_statistics=fake_statistics
            )
        )

    def test_should_get_interconnect_ports(self):
        fake_ports = [dict(t=1), dict(t=2)]

        self.interconnects.get_by.return_value = MOCK_INTERCONNECTS
        self.interconnects.get_ports.return_value = fake_ports

        self.mock_ansible_module.params = self.PARAMS_GET_ALL_PORTS

        InterconnectFactsModule().run()

        self.interconnects.get_by.assert_called_once_with('name', INTERCONNECT_NAME)
        self.interconnects.get_ports.assert_called_once_with(INTERCONNECT_URI)

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(interconnects=MOCK_INTERCONNECTS, interconnect_ports=fake_ports)
        )

    def test_should_get_interconnect_port(self):
        fake_port = dict(t=1)
        port_id = "53fa7d35-1cc8-46c1-abf0-6af091a1aed3:d1"

        self.interconnects.get_by.return_value = MOCK_INTERCONNECTS
        self.interconnects.get_port.return_value = fake_port

        self.mock_ansible_module.params = self.PARAMS_GET_PORT

        InterconnectFactsModule().run()

        self.interconnects.get_by.assert_called_once_with('name', INTERCONNECT_NAME)
        self.interconnects.get_port.assert_called_once_with(INTERCONNECT_URI, port_id)

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(interconnects=MOCK_INTERCONNECTS, interconnect_port=fake_port)
        )


if __name__ == '__main__':
    unittest.main()
