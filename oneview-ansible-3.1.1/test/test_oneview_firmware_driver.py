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

from oneview_firmware_driver import FirmwareDriverModule, FIRMWARE_DRIVER_DELETED, FIRMWARE_DRIVER_ALREADY_ABSENT

from test.utils import ModuleContructorTestCase
from test.utils import ErrorHandlingTestCase

FIRMWARE_DRIVER_NAME = "Service Pack for ProLiant.iso"

PARAMS_ABSENT = dict(
    config='config.json',
    state='absent',
    name=FIRMWARE_DRIVER_NAME
)

FIRMWARE_DRIVER = dict(name=FIRMWARE_DRIVER_NAME)


class FirmwareDriverModuleSpec(unittest.TestCase,
                               ModuleContructorTestCase,
                               ErrorHandlingTestCase):

    def setUp(self):
        self.configure_mocks(self, FirmwareDriverModule)
        ErrorHandlingTestCase.configure(self, method_to_fire=self.mock_ov_client.firmware_drivers.get_by)

    def test_should_remove_firmware_driver(self):
        firmwares = [FIRMWARE_DRIVER]
        self.mock_ov_client.firmware_drivers.get_by.return_value = firmwares
        self.mock_ansible_module.params = PARAMS_ABSENT

        FirmwareDriverModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=FIRMWARE_DRIVER_DELETED
        )

    def test_should_do_nothing_when_firmware_driver_not_exist(self):
        self.mock_ov_client.firmware_drivers.get_by.return_value = []
        self.mock_ansible_module.params = PARAMS_ABSENT

        FirmwareDriverModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=FIRMWARE_DRIVER_ALREADY_ABSENT
        )


if __name__ == '__main__':
    unittest.main()
