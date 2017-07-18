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
from test.utils import PreloadedMocksBaseTestCase, ModuleContructorTestCase, ErrorHandlingTestCase
from copy import deepcopy
import yaml

from oneview_enclosure import EnclosureModule
from oneview_enclosure import ENCLOSURE_ADDED, ENCLOSURE_ALREADY_EXIST, ENCLOSURE_UPDATED, \
    ENCLOSURE_REMOVED, ENCLOSURE_ALREADY_ABSENT, ENCLOSURE_RECONFIGURED, ENCLOSURE_REFRESHED, \
    ENCLOSURE_NOT_FOUND, APPLIANCE_BAY_POWERED_ON, APPLIANCE_BAY_ALREADY_POWERED_ON, UID_ALREADY_POWERED_ON, \
    UID_POWERED_ON, UID_POWERED_OFF, UID_ALREADY_POWERED_OFF, MANAGER_BAY_UID_ALREADY_ON, \
    MANAGER_BAY_UID_ON, BAY_NOT_FOUND, MANAGER_BAY_UID_OFF, MANAGER_BAY_UID_ALREADY_OFF, \
    MANAGER_BAY_POWER_STATE_E_FUSED, MANAGER_BAY_POWER_STATE_RESET, APPLIANCE_BAY_POWER_STATE_E_FUSED, \
    DEVICE_BAY_POWER_STATE_E_FUSED, DEVICE_BAY_POWER_STATE_RESET, INTERCONNECT_BAY_POWER_STATE_E_FUSE, \
    DEVICE_BAY_IPV4_SETTING_REMOVED, INTERCONNECT_BAY_IPV4_SETTING_REMOVED, SUPPORT_DATA_COLLECTION_STATE_ALREADY_SET, \
    SUPPORT_DATA_COLLECTION_STATE_SET

FAKE_MSG_ERROR = 'Fake message error'

DEFAULT_ENCLOSURE_NAME = 'Test-Enclosure'
PRIMARY_IP_ADDRESS = '172.18.1.13'
STANDBY_IP_ADDRESS = '172.18.1.14'

ENCLOSURE_FROM_ONEVIEW = dict(
    name='Encl1',
    uri='/a/path',
    applianceBayCount=2,
    uidState='Off',
    applianceBays=[
        dict(bayNumber=1, poweredOn=True, bayPowerState='Unknown'),
        dict(bayNumber=2, poweredOn=False, bayPowerState='Unknown')
    ],
    managerBays=[
        dict(bayNumber=1, uidState='On', bayPowerState='Unknown'),
        dict(bayNumber=2, uidState='Off', bayPowerState='Unknown')
    ],
    deviceBays=[
        dict(bayNumber=1, bayPowerState='Unknown'),
        dict(bayNumber=2, bayPowerState='Unknown')
    ],
    interconnectBays=[
        dict(bayNumber=1, bayPowerState='Unknown'),
        dict(bayNumber=2, bayPowerState='Unknown')
    ],
    supportDataCollectionState='Completed',
    activeOaPreferredIP=PRIMARY_IP_ADDRESS,
    standbyOaPreferredIP=STANDBY_IP_ADDRESS
)

ALL_ENCLOSURES = [dict(name='Encl3', uri='/a/path3', activeOaPreferredIP='172.18.1.3'),
                  dict(name='Encl2', uri='/a/path2', activeOaPreferredIP='172.18.1.2'),
                  ENCLOSURE_FROM_ONEVIEW]

PARAMS_FOR_PRESENT = dict(
    config='config.json',
    state='present',
    data=dict(name='Encl1',
              hostname=PRIMARY_IP_ADDRESS,
              username='admin',
              password='password123')
)

PARAMS_FOR_PRESENT_NO_HOSTNAME = dict(
    config='config.json',
    state='present',
    data=dict(name='Encl1')
)

PARAMS_WITH_NEW_NAME = dict(
    config='config.json',
    state='present',
    data=dict(name=DEFAULT_ENCLOSURE_NAME,
              newName='OneView-Enclosure')
)

PARAMS_WITH_NEW_RACK_NAME = dict(
    config='config.json',
    state='present',
    data=dict(name='Encl1',
              rackName='Another-Rack-Name')
)

PARAMS_WITH_CALIBRATED_MAX_POWER = dict(
    config='config.json',
    state='present',
    data=dict(name='Encl1',
              calibratedMaxPower=1750)
)

PARAMS_FOR_ABSENT = dict(
    config='config.json',
    state='absent',
    data=dict(name=DEFAULT_ENCLOSURE_NAME)
)

PARAMS_FOR_RECONFIGURED = dict(
    config='config.json',
    state='reconfigured',
    data=dict(name=DEFAULT_ENCLOSURE_NAME)
)

PARAMS_FOR_REFRESH = dict(
    config='config.json',
    state='refreshed',
    data=dict(name=DEFAULT_ENCLOSURE_NAME,
              refreshState='Refreshing')
)


class EnclosureBasicConfigurationSpec(unittest.TestCase,
                                      ModuleContructorTestCase,
                                      ErrorHandlingTestCase):
    """
    Test the module constructor
    ModuleContructorTestCase has common tests for class constructor and main function

    ErrorHandlingTestCase has common tests for the module error handling.
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        ErrorHandlingTestCase.configure(self, method_to_fire=self.mock_ov_client.enclosures.get_by)


class EnclosurePresentStateSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_create_new_enclosure(self):
        self.enclosures.get_by.return_value = []
        self.enclosures.get_all.return_value = []
        self.enclosures.add.return_value = ENCLOSURE_FROM_ONEVIEW
        self.enclosures.patch.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = PARAMS_FOR_PRESENT

        EnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ENCLOSURE_ADDED,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW)
        )

    def test_should_not_update_when_no_changes_by_primary_ip_key(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.get_all.return_value = ALL_ENCLOSURES

        self.mock_ansible_module.params = PARAMS_FOR_PRESENT

        EnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=ENCLOSURE_ALREADY_EXIST,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW)
        )

    def test_should_not_update_when_no_changes_by_standby_ip_key(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.get_all.return_value = ALL_ENCLOSURES

        params = deepcopy(PARAMS_FOR_PRESENT)
        params['data']['hostname'] = STANDBY_IP_ADDRESS
        self.mock_ansible_module.params = params

        EnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=ENCLOSURE_ALREADY_EXIST,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW)
        )

    def test_should_not_update_when_no_changes_by_name_key(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.get_all.return_value = ALL_ENCLOSURES

        self.mock_ansible_module.params = PARAMS_FOR_PRESENT_NO_HOSTNAME

        EnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=ENCLOSURE_ALREADY_EXIST,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW)
        )

    def test_update_when_data_has_new_name(self):
        updated_data = ENCLOSURE_FROM_ONEVIEW.copy()
        updated_data['name'] = 'Test-Enclosure-Renamed'

        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.get_all.return_value = ALL_ENCLOSURES
        self.enclosures.patch.return_value = updated_data

        self.mock_ansible_module.params = PARAMS_WITH_NEW_NAME

        EnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ENCLOSURE_UPDATED,
            ansible_facts=dict(enclosure=updated_data)
        )

    def test_update_when_data_has_new_rack_name(self):
        updated_data = ENCLOSURE_FROM_ONEVIEW.copy()
        updated_data['rackName'] = 'Another-Rack-Name'

        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.get_all.return_value = ALL_ENCLOSURES
        self.enclosures.patch.return_value = updated_data

        self.mock_ansible_module.params = PARAMS_WITH_NEW_RACK_NAME

        EnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ENCLOSURE_UPDATED,
            ansible_facts=dict(enclosure=updated_data)
        )

    def test_replace_name_for_new_enclosure(self):
        self.enclosures.get_by.return_value = []
        self.enclosures.get_all.return_value = []
        self.enclosures.add.return_value = ENCLOSURE_FROM_ONEVIEW
        self.enclosures.patch.return_value = []

        params_ansible = deepcopy(PARAMS_FOR_PRESENT)
        params_ansible['data']['name'] = 'Encl1-Renamed'
        self.mock_ansible_module.params = params_ansible

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            "/a/path", "replace", "/name", "Encl1-Renamed")

    def test_replace_name_for_existent_enclosure(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = []

        self.mock_ansible_module.params = PARAMS_WITH_NEW_NAME

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            "/a/path", "replace", "/name", "OneView-Enclosure")

    def test_replace_rack_name_for_new_enclosure(self):
        updated_data = ENCLOSURE_FROM_ONEVIEW.copy()
        updated_data['rackName'] = 'Another-Rack-Name'

        self.enclosures.get_by.return_value = []
        self.enclosures.get_all.return_value = []
        self.enclosures.add.return_value = ENCLOSURE_FROM_ONEVIEW
        self.enclosures.patch.return_value = []

        params_ansible = deepcopy(PARAMS_FOR_PRESENT)
        params_ansible['data']['rackName'] = 'Another-Rack-Name'
        self.mock_ansible_module.params = params_ansible

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            "/a/path", "replace", "/rackName", "Another-Rack-Name")

    def test_replace_rack_name_for_existent_enclosure(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = []

        self.mock_ansible_module.params = PARAMS_WITH_NEW_RACK_NAME

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            "/a/path", "replace", "/rackName", "Another-Rack-Name")

    def test_update_calibrated_max_power_for_existent_enclosure(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = []

        self.mock_ansible_module.params = PARAMS_WITH_CALIBRATED_MAX_POWER

        EnclosureModule().run()

        self.enclosures.update_environmental_configuration.assert_called_once_with(
            "/a/path", {"calibratedMaxPower": 1750})


class EnclosureAbsentStateSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_remove_enclosure(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        self.mock_ansible_module.params = PARAMS_FOR_ABSENT

        EnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ENCLOSURE_REMOVED
        )

    def test_should_do_nothing_when_enclosure_not_exist(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = PARAMS_FOR_ABSENT

        EnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=ENCLOSURE_ALREADY_ABSENT
        )


class EnclosureReconfiguredStateSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_reconfigure_enclosure(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.update_configuration.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = PARAMS_FOR_RECONFIGURED
        EnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=ENCLOSURE_RECONFIGURED,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW)
        )

    def test_should_fail_when_enclosure_not_exist(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = PARAMS_FOR_RECONFIGURED
        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class EnclosureRefreshedStateSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_refresh_enclosure(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.get.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = PARAMS_FOR_REFRESH

        EnclosureModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=ENCLOSURE_REFRESHED
        )

    def test_should_fail_when_enclosure_not_exist(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = PARAMS_FOR_REFRESH
        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class EnclosureApplianceBaysPowerOnStateSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    PARAMS_FOR_BAY_POWER_ON = dict(
        config='config.json',
        state='appliance_bays_powered_on',
        data=dict(name=DEFAULT_ENCLOSURE_NAME,
                  bayNumber=2)
    )

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_power_on_appliance_bays(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = self.PARAMS_FOR_BAY_POWER_ON

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            ENCLOSURE_FROM_ONEVIEW['uri'], operation='replace', path='/applianceBays/2/power', value='On')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=APPLIANCE_BAY_POWERED_ON
        )

    def test_should_not_power_on_when_state_is_already_on(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        params_power_on_do_nothing = deepcopy(self.PARAMS_FOR_BAY_POWER_ON)
        params_power_on_do_nothing['data']['bayNumber'] = 1
        self.mock_ansible_module.params = params_power_on_do_nothing

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=APPLIANCE_BAY_ALREADY_POWERED_ON
        )

    def test_should_fail_when_appliance_bay_not_found(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        params_power_on_not_found_bay = deepcopy(self.PARAMS_FOR_BAY_POWER_ON)
        params_power_on_not_found_bay['data']['bayNumber'] = 3
        self.mock_ansible_module.params = params_power_on_not_found_bay

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_there_are_not_appliance_bays(self):
        enclosure_without_appliance_bays = dict(ENCLOSURE_FROM_ONEVIEW, applianceBays=[])
        self.enclosures.get_by.return_value = [enclosure_without_appliance_bays]

        self.mock_ansible_module.params = self.PARAMS_FOR_BAY_POWER_ON

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_enclosure_not_found(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = self.PARAMS_FOR_BAY_POWER_ON

        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class EnclosureUidOnStateSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    PARAMS_FOR_UID_ON = """
        config: "{{ config_file_path }}"
        state: uid_on
        data:
          name: 'Test-Enclosure'
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_turn_on_uid(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_UID_ON)

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            ENCLOSURE_FROM_ONEVIEW['uri'], operation='replace', path='/uidState', value='On')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=UID_POWERED_ON
        )

    def test_should_not_set_to_on_when_it_is_already_on(self):
        enclosure_uid_on = dict(ENCLOSURE_FROM_ONEVIEW, uidState='On')
        self.enclosures.get_by.return_value = [enclosure_uid_on]

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_UID_ON)

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(enclosure=enclosure_uid_on),
            msg=UID_ALREADY_POWERED_ON
        )

    def test_should_fail_when_enclosure_not_found(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_UID_ON)

        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class EnclosureUidOffStateSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    PARAMS_FOR_UID_OFF = """
        config: "{{ config_file_path }}"
        state: uid_off
        data:
          name: 'Test-Enclosure'
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_turn_off_uid(self):
        enclosure_uid_on = dict(ENCLOSURE_FROM_ONEVIEW, uidState='On')

        self.enclosures.get_by.return_value = [enclosure_uid_on]
        self.enclosures.patch.return_value = enclosure_uid_on

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_UID_OFF)

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            ENCLOSURE_FROM_ONEVIEW['uri'], operation='replace', path='/uidState', value='Off')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=enclosure_uid_on),
            msg=UID_POWERED_OFF
        )

    def test_should_not_set_to_off_when_it_is_already_off(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_UID_OFF)

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=UID_ALREADY_POWERED_OFF
        )

    def test_should_fail_when_enclosure_not_found(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_UID_OFF)

        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class EnclosureManagerBaysUidOnStateSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    PARAMS_FOR_MANAGER_BAY_UID_ON = """
        config: "{{ config_file_path }}"
        state: manager_bays_uid_on
        data:
          name: 'Test-Enclosure'
          bayNumber: 2
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_turn_on_uid(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_MANAGER_BAY_UID_ON)

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            ENCLOSURE_FROM_ONEVIEW['uri'], operation='replace', path='/managerBays/2/uidState', value='On')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=MANAGER_BAY_UID_ON
        )

    def test_should_not_set_to_on_when_state_already_on(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        params_manager_bay_uid = yaml.load(self.PARAMS_FOR_MANAGER_BAY_UID_ON)
        params_manager_bay_uid['data']['bayNumber'] = '1'

        self.mock_ansible_module.params = params_manager_bay_uid

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=MANAGER_BAY_UID_ALREADY_ON
        )

    def test_should_fail_when_manager_bay_not_found(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        params_power_on_not_found_bay = yaml.load(self.PARAMS_FOR_MANAGER_BAY_UID_ON)
        params_power_on_not_found_bay['data']['bayNumber'] = 3
        self.mock_ansible_module.params = params_power_on_not_found_bay

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_there_are_not_manager_bays(self):
        enclosure_without_appliance_bays = dict(ENCLOSURE_FROM_ONEVIEW, managerBays=[])
        self.enclosures.get_by.return_value = [enclosure_without_appliance_bays]

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_MANAGER_BAY_UID_ON)

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_enclosure_not_found(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_MANAGER_BAY_UID_ON)

        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class EnclosureManagerBaysUidOffStateSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    PARAMS_FOR_MANAGER_BAY_UID_OFF = """
        config: "{{ config_file_path }}"
        state: manager_bays_uid_off
        data:
          name: 'Test-Enclosure'
          bayNumber: 1
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_turn_off_uid(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_MANAGER_BAY_UID_OFF)

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            ENCLOSURE_FROM_ONEVIEW['uri'], operation='replace', path='/managerBays/1/uidState', value='Off')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=MANAGER_BAY_UID_OFF
        )

    def test_should_not_set_to_off_when_state_already_off(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        params_manager_bay_uid = yaml.load(self.PARAMS_FOR_MANAGER_BAY_UID_OFF)
        params_manager_bay_uid['data']['bayNumber'] = '2'

        self.mock_ansible_module.params = params_manager_bay_uid

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=MANAGER_BAY_UID_ALREADY_OFF
        )

    def test_should_fail_when_manager_bay_not_found(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        params_power_on_not_found_bay = yaml.load(self.PARAMS_FOR_MANAGER_BAY_UID_OFF)
        params_power_on_not_found_bay['data']['bayNumber'] = 3
        self.mock_ansible_module.params = params_power_on_not_found_bay

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_there_are_not_manager_bays(self):
        enclosure_without_appliance_bays = dict(ENCLOSURE_FROM_ONEVIEW, managerBays=[])
        self.enclosures.get_by.return_value = [enclosure_without_appliance_bays]

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_MANAGER_BAY_UID_OFF)

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_enclosure_not_found(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_MANAGER_BAY_UID_OFF)

        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class EnclosureManagerBaysPowerStateEFuseSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    PARAMS_FOR_MANAGER_BAY_POWER_STATE_E_FUSE = """
        config: "{{ config_file_path }}"
        state: manager_bays_power_state_e_fuse
        data:
          name: 'Test-Enclosure'
          bayNumber: 1
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_perform_an_e_fuse(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_MANAGER_BAY_POWER_STATE_E_FUSE)

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            ENCLOSURE_FROM_ONEVIEW['uri'], operation='replace', path='/managerBays/1/bayPowerState', value='E-Fuse')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=MANAGER_BAY_POWER_STATE_E_FUSED
        )

    def test_should_fail_when_manager_bay_not_found(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        params_power_on_not_found_bay = yaml.load(self.PARAMS_FOR_MANAGER_BAY_POWER_STATE_E_FUSE)
        params_power_on_not_found_bay['data']['bayNumber'] = 3
        self.mock_ansible_module.params = params_power_on_not_found_bay

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_there_are_not_manager_bays(self):
        enclosure_without_appliance_bays = dict(ENCLOSURE_FROM_ONEVIEW, managerBays=[])
        self.enclosures.get_by.return_value = [enclosure_without_appliance_bays]

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_MANAGER_BAY_POWER_STATE_E_FUSE)

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_enclosure_not_found(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_MANAGER_BAY_POWER_STATE_E_FUSE)

        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class EnclosureManagerBaysPowerStateResetSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    PARAMS_FOR_MANAGER_BAY_POWER_STATE_RESET = """
        config: "{{ config_file_path }}"
        state: manager_bays_power_state_reset
        data:
          name: 'Test-Enclosure'
          bayNumber: 1
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_reset(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_MANAGER_BAY_POWER_STATE_RESET)

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            ENCLOSURE_FROM_ONEVIEW['uri'], operation='replace', path='/managerBays/1/bayPowerState', value='Reset')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=MANAGER_BAY_POWER_STATE_RESET
        )

    def test_should_fail_when_manager_bay_not_found(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        params_power_on_not_found_bay = yaml.load(self.PARAMS_FOR_MANAGER_BAY_POWER_STATE_RESET)
        params_power_on_not_found_bay['data']['bayNumber'] = 3
        self.mock_ansible_module.params = params_power_on_not_found_bay

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_there_are_not_manager_bays(self):
        enclosure_without_appliance_bays = dict(ENCLOSURE_FROM_ONEVIEW, managerBays=[])
        self.enclosures.get_by.return_value = [enclosure_without_appliance_bays]

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_MANAGER_BAY_POWER_STATE_RESET)

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_enclosure_not_found(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_MANAGER_BAY_POWER_STATE_RESET)

        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class EnclosureApplianceBaysPowerStateEFuseSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    PARAMS_FOR_APPLIANCE_BAY_POWER_STATE_E_FUSE = """
        config: "{{ config_file_path }}"
        state: appliance_bays_power_state_e_fuse
        data:
          name: 'Test-Enclosure'
          bayNumber: 1
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_perform_an_e_fuse(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_APPLIANCE_BAY_POWER_STATE_E_FUSE)

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            ENCLOSURE_FROM_ONEVIEW['uri'], operation='replace', path='/applianceBays/1/bayPowerState', value='E-Fuse')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=APPLIANCE_BAY_POWER_STATE_E_FUSED
        )

    def test_should_fail_when_appliance_bay_not_found(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        params_power_on_not_found_bay = yaml.load(self.PARAMS_FOR_APPLIANCE_BAY_POWER_STATE_E_FUSE)
        params_power_on_not_found_bay['data']['bayNumber'] = 3
        self.mock_ansible_module.params = params_power_on_not_found_bay

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_there_are_not_appliance_bays(self):
        enclosure_without_appliance_bays = dict(ENCLOSURE_FROM_ONEVIEW, applianceBays=[])
        self.enclosures.get_by.return_value = [enclosure_without_appliance_bays]

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_APPLIANCE_BAY_POWER_STATE_E_FUSE)

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_enclosure_not_found(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_APPLIANCE_BAY_POWER_STATE_E_FUSE)

        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class DeviceBaysPowerStateEFuseSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    PARAMS_FOR_DEVICE_BAY_POWER_STATE_E_FUSE = """
        config: "{{ config_file_path }}"
        state: device_bays_power_state_e_fuse
        data:
          name: 'Test-Enclosure'
          bayNumber: 1
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_perform_an_e_fuse(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_DEVICE_BAY_POWER_STATE_E_FUSE)

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            ENCLOSURE_FROM_ONEVIEW['uri'], operation='replace', path='/deviceBays/1/bayPowerState', value='E-Fuse')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=DEVICE_BAY_POWER_STATE_E_FUSED
        )

    def test_should_fail_when_device_bay_not_found(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        params_power_on_not_found_bay = yaml.load(self.PARAMS_FOR_DEVICE_BAY_POWER_STATE_E_FUSE)
        params_power_on_not_found_bay['data']['bayNumber'] = 3
        self.mock_ansible_module.params = params_power_on_not_found_bay

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_there_are_not_device_bays(self):
        enclosure_without_appliance_bays = dict(ENCLOSURE_FROM_ONEVIEW, deviceBays=[])
        self.enclosures.get_by.return_value = [enclosure_without_appliance_bays]

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_DEVICE_BAY_POWER_STATE_E_FUSE)

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_enclosure_not_found(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_DEVICE_BAY_POWER_STATE_E_FUSE)

        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class DeviceBaysPowerStateResetSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    PARAMS_FOR_DEVICE_BAY_POWER_STATE_RESET = """
        config: "{{ config_file_path }}"
        state: device_bays_power_state_reset
        data:
          name: 'Test-Enclosure'
          bayNumber: 1
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_reset(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_DEVICE_BAY_POWER_STATE_RESET)

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            ENCLOSURE_FROM_ONEVIEW['uri'], operation='replace', path='/deviceBays/1/bayPowerState', value='Reset')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=DEVICE_BAY_POWER_STATE_RESET
        )

    def test_should_fail_when_device_bay_not_found(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        params_power_on_not_found_bay = yaml.load(self.PARAMS_FOR_DEVICE_BAY_POWER_STATE_RESET)
        params_power_on_not_found_bay['data']['bayNumber'] = 3
        self.mock_ansible_module.params = params_power_on_not_found_bay

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_there_are_not_device_bays(self):
        enclosure_without_appliance_bays = dict(ENCLOSURE_FROM_ONEVIEW, deviceBays=[])
        self.enclosures.get_by.return_value = [enclosure_without_appliance_bays]

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_DEVICE_BAY_POWER_STATE_RESET)

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_enclosure_not_found(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_DEVICE_BAY_POWER_STATE_RESET)

        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class InterconnectBaysPowerStateEFuseSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    PARAMS_FOR_INTERCONNECT_BAY_POWER_STATE_E_FUSE = """
        config: "{{ config_file_path }}"
        state: interconnect_bays_power_state_e_fuse
        data:
          name: 'Test-Enclosure'
          bayNumber: 2
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_perform_an_e_fuse(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_INTERCONNECT_BAY_POWER_STATE_E_FUSE)

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            ENCLOSURE_FROM_ONEVIEW['uri'], operation='replace', path='/interconnectBays/2/bayPowerState',
            value='E-Fuse')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=INTERCONNECT_BAY_POWER_STATE_E_FUSE
        )

    def test_should_fail_when_interconnect_bay_not_found(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        params_power_on_not_found_bay = yaml.load(self.PARAMS_FOR_INTERCONNECT_BAY_POWER_STATE_E_FUSE)
        params_power_on_not_found_bay['data']['bayNumber'] = 3
        self.mock_ansible_module.params = params_power_on_not_found_bay

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_there_are_not_interconnect_bays(self):
        enclosure_without_appliance_bays = dict(ENCLOSURE_FROM_ONEVIEW, interconnectBays=[])
        self.enclosures.get_by.return_value = [enclosure_without_appliance_bays]

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_INTERCONNECT_BAY_POWER_STATE_E_FUSE)

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_enclosure_not_found(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_INTERCONNECT_BAY_POWER_STATE_E_FUSE)

        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class DeviceBaysIpv4RemovedStateSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    PARAMS_FOR_DEVICE_BAY_IPV4_RELEASE = """
        config: "{{ config_file_path }}"
        state: device_bays_ipv4_removed
        data:
          name: 'Test-Enclosure'
          bayNumber: 1
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_remove_ipv4(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_DEVICE_BAY_IPV4_RELEASE)

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            ENCLOSURE_FROM_ONEVIEW['uri'], operation='remove', path='/deviceBays/1/ipv4Setting', value='')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=DEVICE_BAY_IPV4_SETTING_REMOVED
        )

    def test_should_fail_when_device_bay_not_found(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        params_power_on_not_found_bay = yaml.load(self.PARAMS_FOR_DEVICE_BAY_IPV4_RELEASE)
        params_power_on_not_found_bay['data']['bayNumber'] = 3
        self.mock_ansible_module.params = params_power_on_not_found_bay

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_there_are_not_device_bays(self):
        enclosure_without_appliance_bays = dict(ENCLOSURE_FROM_ONEVIEW, deviceBays=[])
        self.enclosures.get_by.return_value = [enclosure_without_appliance_bays]

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_DEVICE_BAY_IPV4_RELEASE)

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_enclosure_not_found(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_DEVICE_BAY_IPV4_RELEASE)

        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class InterconnectBaysIpv4RemovedStateSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    PARAMS_FOR_DEVICE_BAY_IPV4_RELEASE = """
        config: "{{ config_file_path }}"
        state: interconnect_bays_ipv4_removed
        data:
          name: 'Test-Enclosure'
          bayNumber: 1
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_remove_ipv4(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_DEVICE_BAY_IPV4_RELEASE)

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(
            ENCLOSURE_FROM_ONEVIEW['uri'], operation='remove', path='/interconnectBays/1/ipv4Setting', value='')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=INTERCONNECT_BAY_IPV4_SETTING_REMOVED
        )

    def test_should_fail_when_interconnect_bay_not_found(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]

        params_power_on_not_found_bay = yaml.load(self.PARAMS_FOR_DEVICE_BAY_IPV4_RELEASE)
        params_power_on_not_found_bay['data']['bayNumber'] = 3
        self.mock_ansible_module.params = params_power_on_not_found_bay

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_there_are_not_interconnect_bays(self):
        enclosure_without_appliance_bays = dict(ENCLOSURE_FROM_ONEVIEW, interconnectBays=[])
        self.enclosures.get_by.return_value = [enclosure_without_appliance_bays]

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_DEVICE_BAY_IPV4_RELEASE)

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=BAY_NOT_FOUND)

    def test_should_fail_when_enclosure_not_found(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(self.PARAMS_FOR_DEVICE_BAY_IPV4_RELEASE)

        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


class SupportDataCollectionSetStateSpec(unittest.TestCase, PreloadedMocksBaseTestCase):
    PARAMS = """
        config: "{{ config_file_path }}"
        state: support_data_collection_set
        data:
          name: 'Test-Enclosure'
          supportDataCollectionState: 'PendingCollection'
    """

    def setUp(self):
        self.configure_mocks(self, EnclosureModule)
        self.enclosures = self.mock_ov_client.enclosures

    def test_should_set_state(self):
        self.enclosures.get_by.return_value = [ENCLOSURE_FROM_ONEVIEW]
        self.enclosures.patch.return_value = ENCLOSURE_FROM_ONEVIEW

        self.mock_ansible_module.params = yaml.load(self.PARAMS)

        EnclosureModule().run()

        self.enclosures.patch.assert_called_once_with(ENCLOSURE_FROM_ONEVIEW['uri'], operation='replace',
                                                      path='/supportDataCollectionState', value='PendingCollection')

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            ansible_facts=dict(enclosure=ENCLOSURE_FROM_ONEVIEW),
            msg=SUPPORT_DATA_COLLECTION_STATE_SET
        )

    def test_should_not_set_state_when_it_is_already_on_desired_state(self):
        enclosure_uid_on = dict(ENCLOSURE_FROM_ONEVIEW, supportDataCollectionState='PendingCollection')
        self.enclosures.get_by.return_value = [enclosure_uid_on]

        self.mock_ansible_module.params = yaml.load(self.PARAMS)

        EnclosureModule().run()

        self.enclosures.patch.not_been_called()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            ansible_facts=dict(enclosure=enclosure_uid_on),
            msg=SUPPORT_DATA_COLLECTION_STATE_ALREADY_SET
        )

    def test_should_fail_when_enclosure_not_found(self):
        self.enclosures.get_by.return_value = []

        self.mock_ansible_module.params = yaml.load(self.PARAMS)

        EnclosureModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(msg=ENCLOSURE_NOT_FOUND)


if __name__ == '__main__':
    unittest.main()
