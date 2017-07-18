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
import mock

from utils import ModuleContructorTestCase
from utils import ValidateEtagTestCase
from utils import ErrorHandlingTestCase
from oneview_unmanaged_device import (UnmanagedDeviceModule,
                                      UNMANAGED_DEVICE_ADDED,
                                      UNMANAGED_DEVICE_UPDATED,
                                      UNMANAGED_DEVICE_REMOVED,
                                      UNMANAGED_DEVICE_SET_REMOVED,
                                      NOTHING_TO_DO)

ERROR_MSG = "Fake message error"

UNMANAGED_DEVICE_ID = "6a71ad03-70cd-4d2b-9893-fe8e78d79c3c"
UNMANAGED_DEVICE_NAME = "MyUnmanagedDevice"
UNMANAGED_DEVICE_URI = "/rest/unmanaged-devices/" + UNMANAGED_DEVICE_ID

FILTER = "name matches '%'"

UNMANAGED_DEVICE_FOR_PRESENT = dict(
    name=UNMANAGED_DEVICE_NAME,
    model="Procurve 4200VL",
    deviceType="Server"
)

PARAMS_FOR_PRESENT = dict(
    config='config.json',
    state='present',
    data=UNMANAGED_DEVICE_FOR_PRESENT
)

PARAMS_FOR_ABSENT = dict(
    config='config.json',
    state='absent',
    data=dict(name=UNMANAGED_DEVICE_NAME)
)

PARAMS_FOR_REMOVE_ALL = dict(
    config='config.json',
    state='absent',
    data=dict(filter=FILTER)
)

UNMANAGED_DEVICE = dict(
    category="unmanaged-devices",
    deviceType="Server",
    id=UNMANAGED_DEVICE_ID,
    model="Procurve 4200VL",
    name=UNMANAGED_DEVICE_NAME,
    state="Unmanaged",
    status="Disabled",
    uri=UNMANAGED_DEVICE_URI,
)


class UnmanagedDeviceSpec(unittest.TestCase,
                          ModuleContructorTestCase,
                          ValidateEtagTestCase,
                          ErrorHandlingTestCase):
    """
    ModuleContructorTestCase has common tests for class constructor and main function
    ValidateEtagTestCase has common tests for the validate_etag attribute, also provides the mocks used in this test
    case.
    """

    def setUp(self):
        self.configure_mocks(self, UnmanagedDeviceModule)
        self.resource = self.mock_ov_client.unmanaged_devices
        ErrorHandlingTestCase.configure(self, method_to_fire=self.mock_ov_client.unmanaged_devices.get_by)

    def test_should_add(self):
        self.resource.get_by.return_value = []
        self.resource.add.return_value = UNMANAGED_DEVICE

        self.mock_ansible_module.params = PARAMS_FOR_PRESENT

        UnmanagedDeviceModule().run()

        self.resource.get_by.assert_called_once_with('name', UNMANAGED_DEVICE_NAME)

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=UNMANAGED_DEVICE_ADDED,
            ansible_facts=dict(unmanaged_device=UNMANAGED_DEVICE)
        )

    @mock.patch('oneview_unmanaged_device.resource_compare')
    def test_should_not_update_when_data_is_equals(self, mock_resource_compare):
        self.resource.get_by.return_value = [UNMANAGED_DEVICE_FOR_PRESENT]

        self.mock_ansible_module.params = PARAMS_FOR_PRESENT

        mock_resource_compare.return_value = True

        UnmanagedDeviceModule().run()

        self.resource.get_by.assert_called_once_with('name', UNMANAGED_DEVICE_NAME)

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=NOTHING_TO_DO,
            ansible_facts=dict(unmanaged_device=UNMANAGED_DEVICE_FOR_PRESENT)
        )

    @mock.patch('oneview_unmanaged_device.resource_compare')
    def test_should_update_the_unmanaged_device(self, mock_resource_compare):
        self.resource.get_by.return_value = [UNMANAGED_DEVICE_FOR_PRESENT]
        self.resource.update.return_value = UNMANAGED_DEVICE

        params_update = PARAMS_FOR_PRESENT.copy()
        params_update['data']['newName'] = 'UD New Name'

        self.mock_ansible_module.params = params_update

        mock_resource_compare.return_value = False

        UnmanagedDeviceModule().run()

        self.resource.get_by.assert_called_once_with('name', UNMANAGED_DEVICE_NAME)
        self.resource.update.assert_called_once_with(UNMANAGED_DEVICE_FOR_PRESENT)

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=UNMANAGED_DEVICE_UPDATED,
            ansible_facts=dict(unmanaged_device=UNMANAGED_DEVICE)
        )

    def test_should_remove_the_unmanaged_device(self):
        self.resource.get_by.return_value = [UNMANAGED_DEVICE]
        self.resource.remove.return_value = True

        self.mock_ansible_module.params = PARAMS_FOR_ABSENT

        UnmanagedDeviceModule().run()

        self.resource.remove.assert_called_once_with(UNMANAGED_DEVICE)

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=UNMANAGED_DEVICE_REMOVED
        )

    def test_should_do_nothing_when_not_exist(self):
        self.resource.get_by.return_value = []

        self.mock_ansible_module.params = PARAMS_FOR_ABSENT

        UnmanagedDeviceModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=NOTHING_TO_DO
        )

    def test_should_delete_all_resources(self):
        self.resource.remove_all.return_value = [UNMANAGED_DEVICE]

        self.mock_ansible_module.params = PARAMS_FOR_REMOVE_ALL

        UnmanagedDeviceModule().run()

        self.resource.remove_all.assert_called_once_with(filter=FILTER)

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=UNMANAGED_DEVICE_SET_REMOVED
        )


if __name__ == '__main__':
    unittest.main()
