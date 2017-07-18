#!/usr/bin/python
# -*- coding: utf-8 -*-
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
from ansible.module_utils.basic import *
try:
    from hpOneView.oneview_client import OneViewClient
    from hpOneView.extras.comparators import resource_compare
    from hpOneView.exceptions import HPOneViewException
    from hpOneView.exceptions import HPOneViewValueError

    HAS_HPE_ONEVIEW = True
except ImportError:
    HAS_HPE_ONEVIEW = False

DOCUMENTATION = '''
---
module: oneview_storage_volume_template
short_description: Manage OneView Storage Volume Template resources.
description:
    - "Provides an interface to manage Storage Volume Template resources. Can create, update and delete."
requirements:
    - "python >= 2.7.9"
    - "hpOneView >= 3.1.0"
author: "Gustavo Hennig (@GustavoHennig)"
options:
    config:
      description:
        - Path to a .json configuration file containing the OneView client configuration.
          The configuration file is optional. If the file path is not provided, the configuration will be loaded from
          environment variables.
      required: false
    state:
        description:
            - Indicates the desired state for the Storage Volume Template resource.
              'present' will ensure data properties are compliant with OneView.
              'absent' will remove the resource from OneView, if it exists.
        choices: ['present', 'absent']
        required: true
    data:
        description:
            - List with Storage Volume Template properties and its associated states.
        required: true
    validate_etag:
        description:
            - When the ETag Validation is enabled, the request will be conditionally processed only if the current ETag
              for the resource matches the ETag provided in the data.
        default: true
        choices: ['true', 'false']
notes:
    - "A sample configuration file for the config parameter can be found at:
       https://github.com/HewlettPackard/oneview-ansible/blob/master/examples/oneview_config-rename.json"
    - "Check how to use environment variables for configuration at:
       https://github.com/HewlettPackard/oneview-ansible#environment-variables"
'''

EXAMPLES = '''
- name: Create a Storage Volume Template
  oneview_storage_volume_template:
    config: "{{ config }}"
    state: present
    data:
        name: 'Volume Template Name'
        state: "Configured"
        description: "Example Template"
        provisioning:
             shareable: true
             provisionType: "Thin"
             capacity: "235834383322"
             storagePoolUri: "/rest/storage-pools/2D69A182-862E-4ECE-8BEE-73E0F5BEC855"
        stateReason: "None"
        storageSystemUri: "/rest/storage-systems/TXQ1010307"
        snapshotPoolUri: "/rest/storage-pools/2D69A182-862E-4ECE-8BEE-73E0F5BEC855"
        type: StorageVolumeTemplateV3
  delegate_to: localhost


- name: Delete the Storage Volume Template
  oneview_storage_volume_template:
    config: "{{ config }}"
    state: absent
    data:
        name: 'Volume Template Name'
  delegate_to: localhost
'''

RETURN = '''
storage_volume_template:
    description: Has the OneView facts about the Storage Volume Template.
    returned: On 'present' state, but can be null.
    type: complex
'''

STORAGE_VOLUME_TEMPLATE_CREATED = 'Storage Volume Template created successfully.'
STORAGE_VOLUME_TEMPLATE_UPDATED = 'Storage Volume Template updated successfully.'
STORAGE_VOLUME_TEMPLATE_ALREADY_UPDATED = 'Storage Volume Template is already updated.'
STORAGE_VOLUME_TEMPLATE_DELETED = 'Storage Volume Template deleted successfully.'
STORAGE_VOLUME_TEMPLATE_ALREADY_ABSENT = 'Storage Volume Template is already absent.'
STORAGE_VOLUME_TEMPLATE_MANDATORY_FIELD_MISSING = "Mandatory field was not informed: data.name"
HPE_ONEVIEW_SDK_REQUIRED = 'HPE OneView Python SDK is required for this module.'


class StorageVolumeTemplateModule(object):
    argument_spec = dict(
        config=dict(required=False, type='str'),
        state=dict(
            required=True,
            choices=['present', 'absent']
        ),
        data=dict(required=True, type='dict'),
        validate_etag=dict(
            required=False,
            type='bool',
            default=True)
    )

    def __init__(self):
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=False
        )
        if not HAS_HPE_ONEVIEW:
            self.module.fail_json(msg=HPE_ONEVIEW_SDK_REQUIRED)

        if not self.module.params['config']:
            self.oneview_client = OneViewClient.from_environment_variables()
        else:
            self.oneview_client = OneViewClient.from_json_file(self.module.params['config'])

    def run(self):
        try:
            state = self.module.params['state']
            data = self.module.params['data']
            changed, msg, ansible_facts = False, '', {}

            if not self.module.params.get('validate_etag'):
                self.oneview_client.connection.disable_etag_validation()

            if not data.get('name'):
                raise HPOneViewValueError(STORAGE_VOLUME_TEMPLATE_MANDATORY_FIELD_MISSING)

            resource = (self.oneview_client.storage_volume_templates.get_by("name", data['name']) or [None])[0]

            if state == 'present':
                changed, msg, ansible_facts = self.__present(data, resource)
            elif state == 'absent':
                changed, msg, ansible_facts = self.__absent(resource)

            self.module.exit_json(changed=changed,
                                  msg=msg,
                                  ansible_facts=ansible_facts)

        except HPOneViewException as exception:
            self.module.fail_json(msg=exception.args[0])

    def __present(self, data, resource):

        changed = False
        msg = ''

        if not resource:
            resource = self.oneview_client.storage_volume_templates.create(data)
            changed = True
            msg = STORAGE_VOLUME_TEMPLATE_CREATED
        else:

            merged_data = resource.copy()
            merged_data.update(data)

            if not resource_compare(resource, merged_data):
                # update resource
                changed = True
                resource = self.oneview_client.storage_volume_templates.update(merged_data)
                msg = STORAGE_VOLUME_TEMPLATE_UPDATED
            else:
                msg = STORAGE_VOLUME_TEMPLATE_ALREADY_UPDATED

        return changed, msg, dict(storage_volume_template=resource)

    def __absent(self, resource):
        if resource:
            self.oneview_client.storage_volume_templates.delete(resource)
            return True, STORAGE_VOLUME_TEMPLATE_DELETED, {}
        else:
            return False, STORAGE_VOLUME_TEMPLATE_ALREADY_ABSENT, {}


def main():
    StorageVolumeTemplateModule().run()


if __name__ == '__main__':
    main()
