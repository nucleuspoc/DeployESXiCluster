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

from oneview_os_deployment_plan_facts import OsDeploymentPlanFactsModule
from test.utils import ModuleContructorTestCase, FactsParamsTestCase, ErrorHandlingTestCase

ERROR_MSG = 'Fake message error'

PARAMS_GET_ALL = dict(
    config='config.json',
    name=None
)

PARAMS_GET_BY_NAME = dict(
    config='config.json',
    name="Test Os Deployment Plan"
)

PARAMS_GET_OPTIONS = {
    "config": 'config.json',
    "name": "Test Os Deployment Plan",
    "options": [
        "osCustomAttributesForServerProfile"]
}

OS_DEPLOYMENT_PLAN = {
    "name": "Test Os Deployment Plan",
    "additionalParameters": [
        {"name": "name1",
         "value": "value1",
         "caEditable": True},
        {"name": "name2",
         "value": "value2",
         "caEditable": False},
        {"name": "name3",
         "value": "value3",
         "caEditable": True}
    ]
}

OS_DEPLOYMENT_PLAN_WITH_NIC = {
    "name": "Test Os Deployment Plan",
    "additionalParameters": [
        {"name": "name1",
         "value": "value1",
         "caEditable": True},
        {"name": "name1",
         "value": "value1",
         "caType": "nic",
         "caEditable": True},
        {"name": "name2",
         "value": "value2",
         "caEditable": False},
        {"name": "name3",
         "value": "value3",
         "caEditable": True}
    ]
}

OS_DEPLOYMENT_PLAN_WITHOUT_EDITABLE = {
    "name": "Test Os Deployment Plan",
    "additionalParameters": [
        {"name": "name2",
         "value": "value2",
         "caEditable": False},
    ]
}


class OsDeploymentPlanFactsSpec(unittest.TestCase,
                                ModuleContructorTestCase,
                                FactsParamsTestCase,
                                ErrorHandlingTestCase):
    """
    ModuleContructorTestCase has common tests for the class constructor and the main function, and also provides the
    mocks used in this test class.

    FactsParamsTestCase has common tests for the parameters support.

    ErrorHandlingTestCase has common tests for the module error handling.
    """

    def setUp(self):
        self.configure_mocks(self, OsDeploymentPlanFactsModule)
        self.resource = self.mock_ov_client.os_deployment_plans
        FactsParamsTestCase.configure_client_mock(self, self.resource)
        ErrorHandlingTestCase.configure(self, method_to_fire=self.resource.get_by)

    def test_should_get_all_os_deployment_plans(self):
        self.resource.get_all.return_value = [{"name": "Os Deployment Plan Name"}]

        self.mock_ansible_module.params = PARAMS_GET_ALL

        OsDeploymentPlanFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(os_deployment_plans=([{"name": "Os Deployment Plan Name"}]))
        )

    def test_should_get_os_deployment_plan_by_name(self):
        self.resource.get_by.return_value = [{"Os Deployment Plan Name"}]

        self.mock_ansible_module.params = PARAMS_GET_BY_NAME

        OsDeploymentPlanFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(os_deployment_plans=([{"Os Deployment Plan Name"}]))
        )

    def test_should_get_custom_attributes(self):
        self.resource.get_by.return_value = [OS_DEPLOYMENT_PLAN]

        self.mock_ansible_module.params = PARAMS_GET_OPTIONS

        OsDeploymentPlanFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts={'os_deployment_plans': [OS_DEPLOYMENT_PLAN],
                           'os_deployment_plan_custom_attributes':
                               {'os_custom_attributes_for_server_profile': [{'name': 'name1',
                                                                             'value': 'value1'},
                                                                            {'name': 'name3',
                                                                             'value': 'value3'}]
                                }
                           })

    def test_should_get_custom_attributes_without_editable(self):
        self.resource.get_by.return_value = [OS_DEPLOYMENT_PLAN_WITHOUT_EDITABLE]

        self.mock_ansible_module.params = PARAMS_GET_OPTIONS

        OsDeploymentPlanFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts={'os_deployment_plans': [OS_DEPLOYMENT_PLAN_WITHOUT_EDITABLE],
                           'os_deployment_plan_custom_attributes':
                               {'os_custom_attributes_for_server_profile': []}
                           })

    def test_should_get_custom_attributes_with_nic_support(self):
        self.resource.get_by.return_value = [OS_DEPLOYMENT_PLAN_WITH_NIC]

        self.mock_ansible_module.params = PARAMS_GET_OPTIONS

        OsDeploymentPlanFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts={'os_deployment_plans': [OS_DEPLOYMENT_PLAN_WITH_NIC],
                           'os_deployment_plan_custom_attributes':
                               {'os_custom_attributes_for_server_profile':
                                   [
                                       {'name': 'name1', 'value': 'value1'},
                                       {'name': 'name3', 'value': 'value3'},
                                       {'name': 'name1.dhcp', 'value': False},
                                       {'name': 'name1.networkuri', 'value': ''},
                                       {'name': 'name1.connectionid', 'value': ''},
                                       {'name': 'name1.ipv4disable', 'value': False},
                                       {'name': 'name1.constraint', 'value': 'auto'}
                                   ]}
                           }
        )


if __name__ == '__main__':
    unittest.main()
