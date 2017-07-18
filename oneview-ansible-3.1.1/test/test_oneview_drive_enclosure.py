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

from oneview_drive_enclosure import DriveEnclosureModule, DRIVE_ENCLOSURE_NAME_REQUIRED, DRIVE_ENCLOSURE_NOT_FOUND

from utils import ModuleContructorTestCase
from utils import ErrorHandlingTestCase

FAKE_MSG_ERROR = 'Fake message error'

DRIVE_ENCLOSURE_URI = '/rest/drive-enclosures/SN123101'

DICT_DEFAULT_DRIVE_ENCLOSURE = {
    'manufacturer': 'HPE',
    'model': 'Synergy D3940 Storage Module',
    'name': '0000A66102, bay 1',
    'powerState': 'On',
    'productName': 'Storage Enclosure 500143803110129D',
    'refreshState': 'NotRefreshing',
    'serialNumber': 'SN123101',
    'state': 'Monitored',
    'stateReason': None,
    'status': 'OK',
    'temperature': 11,
    'type': 'drive-enclosure',
    'uidState': 'Off',
    'uri': DRIVE_ENCLOSURE_URI,
    'wwid': '500143803110129D'
}

YAML_DRIVE_ENCLOSURE_POWER_STATE = """
    config: "{{ config }}"
    state: power_state_set
    data:
        name: '0000A66102, bay 1'
        powerState: 'Off'
"""

YAML_DRIVE_ENCLOSURE_UID_STATE = """
    config: "{{ config_file_path }}"
    state: uid_state_set
    data:
        name: '0000A66102, bay 1'
        uidState: 'On'
"""

YAML_DRIVE_ENCLOSURE_HARD_RESET_STATE = """
    config: "{{ config_file_path }}"
    state: hard_reset_state_set
    data:
        name: '0000A66102, bay 1'
"""

YAML_DRIVE_ENCLOSURE_REFRESH_STATE = """
    config: "{{ config_file_path }}"
    state: refresh_state_set
    data:
        name: '0000A66102, bay 1'
        refreshState: 'RefreshPending'
"""

YAML_WITHOUT_NAME = """
    config: "{{ config }}"
    state: power_state_set
    data:
        powerState: 'Off'
"""


class DriveEnclosureSpec(unittest.TestCase,
                         ModuleContructorTestCase,
                         ErrorHandlingTestCase):
    def setUp(self):
        self.configure_mocks(self, DriveEnclosureModule)
        self.drive_enclosures = self.mock_ov_client.drive_enclosures

        ErrorHandlingTestCase.configure(self, method_to_fire=self.drive_enclosures.get_by)

    def test_should_raise_exception_when_name_not_defined(self):
        self.mock_ansible_module.params = yaml.load(YAML_WITHOUT_NAME)

        DriveEnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(
            msg=DRIVE_ENCLOSURE_NAME_REQUIRED
        )

    def test_should_raise_exception_when_resource_not_found(self):
        self.drive_enclosures.get_by.return_value = []
        self.mock_ansible_module.params = yaml.load(YAML_DRIVE_ENCLOSURE_POWER_STATE)

        DriveEnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(
            msg=DRIVE_ENCLOSURE_NOT_FOUND
        )

    def test_should_power_off(self):
        mock_return_patch = {'name': 'mock return'}

        self.drive_enclosures.get_by.return_value = [DICT_DEFAULT_DRIVE_ENCLOSURE]
        self.drive_enclosures.patch.return_value = mock_return_patch
        self.mock_ansible_module.params = yaml.load(YAML_DRIVE_ENCLOSURE_POWER_STATE)

        DriveEnclosureModule().run()

        self.drive_enclosures.patch.assert_called_once_with(
            DRIVE_ENCLOSURE_URI, operation='replace', path='/powerState', value='Off')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(drive_enclosure=mock_return_patch)
        )

    def test_should_not_power_off_when_already_off(self):
        drive_enclosure = DICT_DEFAULT_DRIVE_ENCLOSURE.copy()
        drive_enclosure['powerState'] = 'Off'

        self.drive_enclosures.get_by.return_value = [drive_enclosure]
        self.mock_ansible_module.params = yaml.load(YAML_DRIVE_ENCLOSURE_POWER_STATE)

        DriveEnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(drive_enclosure=drive_enclosure)
        )

    def test_should_turn_uid_on(self):
        mock_return_patch = {'name': 'mock return'}

        self.drive_enclosures.get_by.return_value = [DICT_DEFAULT_DRIVE_ENCLOSURE]
        self.drive_enclosures.patch.return_value = mock_return_patch
        self.mock_ansible_module.params = yaml.load(YAML_DRIVE_ENCLOSURE_UID_STATE)

        DriveEnclosureModule().run()

        self.drive_enclosures.patch.assert_called_once_with(
            DRIVE_ENCLOSURE_URI, operation='replace', path='/uidState', value='On')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(drive_enclosure=mock_return_patch)
        )

    def test_should_not_turn_uid_off_when_already_on(self):
        drive_enclosure = DICT_DEFAULT_DRIVE_ENCLOSURE.copy()
        drive_enclosure['uidState'] = 'On'

        self.drive_enclosures.get_by.return_value = [drive_enclosure]
        self.mock_ansible_module.params = yaml.load(YAML_DRIVE_ENCLOSURE_UID_STATE)

        DriveEnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(drive_enclosure=drive_enclosure)
        )

    def test_should_request_hard_reset(self):
        mock_return_patch = {'name': 'mock return'}

        self.drive_enclosures.get_by.return_value = [DICT_DEFAULT_DRIVE_ENCLOSURE]
        self.drive_enclosures.patch.return_value = mock_return_patch
        self.mock_ansible_module.params = yaml.load(YAML_DRIVE_ENCLOSURE_HARD_RESET_STATE)

        DriveEnclosureModule().run()

        self.drive_enclosures.patch.assert_called_once_with(
            DRIVE_ENCLOSURE_URI, operation='replace', path='/hardResetState', value='Reset')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(drive_enclosure=mock_return_patch)
        )

    def test_should_refresh(self):
        mock_return_refresh = {'name': 'mock return'}

        self.drive_enclosures.get_by.return_value = [DICT_DEFAULT_DRIVE_ENCLOSURE]
        self.drive_enclosures.refresh_state.return_value = mock_return_refresh
        self.mock_ansible_module.params = yaml.load(YAML_DRIVE_ENCLOSURE_REFRESH_STATE)

        DriveEnclosureModule().run()

        self.drive_enclosures.refresh_state.assert_called_once_with(
            DRIVE_ENCLOSURE_URI, {'refreshState': 'RefreshPending'})

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(drive_enclosure=mock_return_refresh)
        )


if __name__ == '__main__':
    unittest.main()
