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

from oneview_volume import VolumeModule
from oneview_volume import VOLUME_CREATED, VOLUME_UPDATED, VOLUME_DELETED, VOLUME_ALREADY_ABSENT, VOLUME_REPAIRED, \
    VOLUME_NOT_FOUND, VOLUME_SNAPSHOT_CREATED, VOLUME_SNAPSHOT_DELETED, VOLUME_SNAPSHOT_NOT_FOUND, \
    VOLUME_NEW_NAME_INVALID

from utils import ModuleContructorTestCase
from utils import ValidateEtagTestCase
from utils import ErrorHandlingTestCase


FAKE_MSG_ERROR = 'Fake message error'

EXISTENT_VOLUME = dict(
    name='Volume with Storage Pool',
    description='Test volume with common creation: Storage Pool',
    uri='/rest/storage-volumes/3B1CF17F-7657-4C89-B580-D236507A9182'
)

EXISTENT_VOLUME_WITH_NEW_NAME = dict(
    name='Volume with Storage Pool - Renamed',
    description='Test volume with common creation: Storage Pool',
    uri='/rest/storage-volumes/F28FC559-0896-4D14-A694-DB70C784BB9E'
)

SNAPSHOT_URI = EXISTENT_VOLUME['uri'] + '/snapshots/CA9E652A-A45A-45DA-BD2A-1A7638BF1699'

PARAMS_FOR_CREATE = dict(
    config='config.json',
    state='present',
    data=dict(name='Volume with Storage Pool',
              provisioningParameters=dict(provisionType='Full',
                                          shareable=True,
                                          requestedCapacity=1073741824,
                                          storagePoolUri='/rest/storage-pools/3B1CF17F-7657-4C89-B580-D236507A9182'))
)

PARAMS_FOR_UPDATE = dict(
    config='config.json',
    state='present',
    data=dict(name='Volume with Storage Pool',
              newName='Volume with Storage Pool - Renamed',
              shareable=False)
)

PARAMS_FOR_ABSENT = dict(
    config='config.json',
    state='absent',
    data=dict(name='Volume with Storage Pool')
)

PARAMS_FOR_ABSENT_EXPORT_ONLY = dict(
    config='config.json',
    state='absent',
    data=dict(name='Volume with Storage Pool'),
    export_only=True
)

PARAMS_FOR_REPAIR = dict(
    config='config.json',
    state='repaired',
    data=dict(name='Volume with Storage Pool')
)

PARAMS_FOR_SNAPSHOT_CREATED = dict(
    config='config.json',
    state='snapshot_created',
    data=dict(name='Volume with Storage Pool',
              snapshotParameters=dict(name='filename',
                                      type='Snapshot'))
)

PARAMS_FOR_SNAPSHOT_DELETED = dict(
    config='config.json',
    state='snapshot_deleted',
    data=dict(name='Volume with Storage Pool',
              snapshotParameters=dict(name='filename',
                                      type='Snapshot'))
)


class VolumeModuleSpec(unittest.TestCase,
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
        self.configure_mocks(self, VolumeModule)
        self.resource = self.mock_ov_client.volumes
        ErrorHandlingTestCase.configure(self, method_to_fire=self.resource.get_by)

    def test_should_create_new_volume_when_not_exist(self):
        self.resource.get_by.return_value = []
        self.resource.create.return_value = EXISTENT_VOLUME

        self.mock_ansible_module.params = PARAMS_FOR_CREATE

        VolumeModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=VOLUME_CREATED,
            ansible_facts=dict(storage_volume=EXISTENT_VOLUME)
        )

    def test_should_update_volume_when_already_exist(self):
        self.resource.get_by.side_effect = [EXISTENT_VOLUME], []
        self.resource.update.return_value = EXISTENT_VOLUME.copy()

        self.mock_ansible_module.params = PARAMS_FOR_UPDATE

        VolumeModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=VOLUME_UPDATED,
            ansible_facts=dict(storage_volume=EXISTENT_VOLUME.copy())
        )

    def test_should_raise_exception_when_new_name_already_used(self):
        self.resource.get_by.side_effect = [EXISTENT_VOLUME], [EXISTENT_VOLUME_WITH_NEW_NAME]
        self.resource.update.return_value = EXISTENT_VOLUME.copy()

        self.mock_ansible_module.params = PARAMS_FOR_UPDATE

        VolumeModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(
            msg=VOLUME_NEW_NAME_INVALID
        )

    def test_should_delete_volume(self):
        self.resource.get_by.return_value = [EXISTENT_VOLUME]

        self.mock_ansible_module.params = PARAMS_FOR_ABSENT

        VolumeModule().run()

        self.resource.delete.assert_called_once_with(EXISTENT_VOLUME, export_only=False)

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=VOLUME_DELETED
        )

    def test_should_remove_volume(self):
        self.resource.get_by.return_value = [EXISTENT_VOLUME]

        self.mock_ansible_module.params = PARAMS_FOR_ABSENT_EXPORT_ONLY

        VolumeModule().run()

        self.resource.delete.assert_called_once_with(EXISTENT_VOLUME, export_only=True)

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=VOLUME_DELETED
        )

    def test_should_do_nothing_when_volume_not_exist(self):
        self.resource.get_by.return_value = []

        self.mock_ansible_module.params = PARAMS_FOR_ABSENT

        VolumeModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=False,
            msg=VOLUME_ALREADY_ABSENT
        )

    def test_should_repair_volume(self):
        self.resource.get_by.return_value = [EXISTENT_VOLUME]

        self.mock_ansible_module.params = PARAMS_FOR_REPAIR

        VolumeModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=VOLUME_REPAIRED
        )

    def test_should_create_snapshot(self):
        self.resource.get_by.return_value = [EXISTENT_VOLUME]

        self.mock_ansible_module.params = PARAMS_FOR_SNAPSHOT_CREATED

        VolumeModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=VOLUME_SNAPSHOT_CREATED
        )

    def test_should_not_create_snapshot_when_resource_not_exist(self):
        self.resource.get_by.return_value = []

        self.mock_ansible_module.params = PARAMS_FOR_SNAPSHOT_CREATED

        VolumeModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(
            msg=VOLUME_NOT_FOUND
        )

    def test_should_delete_snapshot(self):
        self.resource.get_by.return_value = [EXISTENT_VOLUME]
        self.resource.get_snapshot_by.return_value = [{'uri': SNAPSHOT_URI}]

        self.mock_ansible_module.params = PARAMS_FOR_SNAPSHOT_DELETED

        VolumeModule().run()

        self.mock_ansible_module.exit_json.assert_called_once_with(
            changed=True,
            msg=VOLUME_SNAPSHOT_DELETED
        )

    def test_should_not_delete_snapshot_when_resource_not_exist(self):
        self.resource.get_by.return_value = []

        self.mock_ansible_module.params = PARAMS_FOR_SNAPSHOT_DELETED

        VolumeModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(
            msg=VOLUME_NOT_FOUND
        )

    def test_should_not_delete_snapshot_when_snapshot_not_exist(self):
        self.resource.get_by.return_value = [EXISTENT_VOLUME]
        self.resource.get_snapshot_by.return_value = []

        self.mock_ansible_module.params = PARAMS_FOR_SNAPSHOT_DELETED

        VolumeModule().run()

        self.mock_ansible_module.fail_json.assert_called_once_with(
            msg=VOLUME_SNAPSHOT_NOT_FOUND
        )


if __name__ == '__main__':
    unittest.main()
