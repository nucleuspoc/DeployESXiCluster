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

from image_streamer_plan_script_facts import PlanScriptFactsModule, EXAMPLES
from utils import ModuleContructorTestCase
from utils import FactsParamsTestCase
from utils import ErrorHandlingTestCase

ERROR_MSG = 'Fake message error'


class PlanScriptFactsSpec(unittest.TestCase,
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
        self.configure_mocks(self, PlanScriptFactsModule)
        self.i3s = self.mock_ov_client.create_image_streamer_client()

        FactsParamsTestCase.configure_client_mock(self, self.i3s.plan_scripts)
        ErrorHandlingTestCase.configure(self, method_to_fire=self.i3s.plan_scripts.get_by)

        # Load scenarios from module examples
        self.PLAN_SCRIPT_FACTS_EXAMPLES = yaml.load(EXAMPLES)

        self.TASK_GET_ALL = self.PLAN_SCRIPT_FACTS_EXAMPLES[0]['image_streamer_plan_script_facts']
        self.TASK_GET_BY_NAME = self.PLAN_SCRIPT_FACTS_EXAMPLES[4]['image_streamer_plan_script_facts']

        self.PLAN_SCRIPT = dict(
            name="Plan Script name",
            uri="/rest/plan-scripts/d1c7b09a-6c7b-4ae0-b68e-ed208ccde1b0")

    def test_get_all_plan_scripts(self):
        self.i3s.plan_scripts.get_all.return_value = [self.PLAN_SCRIPT]
        self.mock_ansible_module.params = self.TASK_GET_ALL

        PlanScriptFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(plan_scripts=[self.PLAN_SCRIPT])
        )

    def test_get_a_plan_script_by_name(self):
        self.i3s.plan_scripts.get_by.return_value = [self.PLAN_SCRIPT]
        self.mock_ansible_module.params = self.TASK_GET_BY_NAME

        PlanScriptFactsModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(plan_scripts=[self.PLAN_SCRIPT])
        )


if __name__ == '__main__':
    unittest.main()
