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

from oneview_sas_interconnect_type_facts import SasInterconnectTypeFactsModule
from test.utils import ModuleContructorTestCase, FactsParamsTestCase, ErrorHandlingTestCase

ERROR_MSG = 'Fake message error'

PARAMS_GET_ALL = dict(
    config='config.json',
    name=None
)

PARAMS_GET_BY_NAME = dict(
    config='config.json',
    name="Type 2"
)

SAS_INTERCONNECT_TYPES = [{"name": "Type 1"}, {"name": "Type 2"}, {"name": "Type 3"}]


class SasInterconnectTypeFactsSpec(unittest.TestCase,
                                   ModuleContructorTestCase,
                                   FactsParamsTestCase,
                                   ErrorHandlingTestCase):
    def setUp(self):
        self.configure_mocks(self, SasInterconnectTypeFactsModule)
        self.resource = self.mock_ov_client.sas_interconnect_types
        FactsParamsTestCase.configure_client_mock(self, self.resource)
        ErrorHandlingTestCase.configure(self, method_to_fire=self.resource.get_by)

    def test_should_get_all_sas_interconnect_types(self):
        self.resource.get_all.return_value = SAS_INTERCONNECT_TYPES
        self.mock_ansible_module.params = PARAMS_GET_ALL

        SasInterconnectTypeFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(sas_interconnect_types=(SAS_INTERCONNECT_TYPES))
        )

    def test_should_get_sas_interconnect_type_by_name(self):
        self.resource.get_by.return_value = [SAS_INTERCONNECT_TYPES[1]]
        self.mock_ansible_module.params = PARAMS_GET_BY_NAME

        SasInterconnectTypeFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(sas_interconnect_types=([SAS_INTERCONNECT_TYPES[1]]))
        )


if __name__ == '__main__':
    unittest.main()
