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

    HAS_HPE_ONEVIEW = True
except ImportError:
    HAS_HPE_ONEVIEW = False

DOCUMENTATION = '''
---
module: oneview_fcoe_network
short_description: Manage OneView FCoE Network resources.
description:
    - Provides an interface to manage FCoE Network resources. Can create, update, or delete.
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
            - Indicates the desired state for the FCoE Network resource.
              'present' will ensure data properties are compliant with OneView.
              'absent' will remove the resource from OneView, if it exists.
        choices: ['present', 'absent']
    data:
        description:
            - List with FCoE Network properties.
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
- name: Ensure that FCoE Network is present using the default configuration
  oneview_fcoe_network:
    config: "{{ config_file_path }}"
    state: present
    data:
      name: 'Test FCoE Network'
      vlanId: '201'

- name: Ensure that FCoE Network is absent
  oneview_fcoe_network:
    config: "{{ config_file_path }}"
    state: absent
    data:
      name: 'New FCoE Network'
'''

RETURN = '''
fcoe_network:
    description: Has the facts about the OneView FCoE Networks.
    returned: On state 'present'. Can be null.
    type: complex
'''

FCOE_NETWORK_CREATED = 'FCoE Network created successfully.'
FCOE_NETWORK_UPDATED = 'FCoE Network updated successfully.'
FCOE_NETWORK_DELETED = 'FCoE Network deleted successfully.'
FCOE_NETWORK_ALREADY_EXIST = 'FCoE Network already exists.'
FCOE_NETWORK_ALREADY_ABSENT = 'Nothing to do.'
HPE_ONEVIEW_SDK_REQUIRED = 'HPE OneView Python SDK is required for this module.'


class FcoeNetworkModule(object):
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
        self.module = AnsibleModule(argument_spec=self.argument_spec, supports_check_mode=False)
        if not HAS_HPE_ONEVIEW:
            self.module.fail_json(msg=HPE_ONEVIEW_SDK_REQUIRED)

        if not self.module.params['config']:
            self.oneview_client = OneViewClient.from_environment_variables()
        else:
            self.oneview_client = OneViewClient.from_json_file(self.module.params['config'])

    def run(self):
        state = self.module.params['state']
        data = self.module.params['data']

        try:

            if not self.module.params.get('validate_etag'):
                self.oneview_client.connection.disable_etag_validation()

            changed, msg, ansible_facts = False, '', {}

            if state == 'present':
                changed, msg, ansible_facts = self.__present(data)
            elif state == 'absent':
                changed, msg, ansible_facts = self.__absent(data)

            self.module.exit_json(changed=changed,
                                  msg=msg,
                                  ansible_facts=ansible_facts)

        except HPOneViewException as exception:
            self.module.fail_json(msg='; '.join(str(e) for e in exception.args))

    def __present(self, data):
        resource = self.__get_by_name(data)
        changed = False

        if "newName" in data:
            data["name"] = data["newName"]
            del data["newName"]

        if not resource:
            resource = self.oneview_client.fcoe_networks.create(data)
            msg = FCOE_NETWORK_CREATED
            changed = True
        else:
            merged_data = resource.copy()
            merged_data.update(data)

            if resource_compare(resource, merged_data):
                msg = FCOE_NETWORK_ALREADY_EXIST
            else:
                resource = self.oneview_client.fcoe_networks.update(merged_data)
                changed = True
                msg = FCOE_NETWORK_UPDATED

        return changed, msg, dict(fcoe_network=resource)

    def __absent(self, data):
        resource = self.__get_by_name(data)

        if resource:
            self.oneview_client.fcoe_networks.delete(resource)
            return True, FCOE_NETWORK_DELETED, {}
        else:
            return False, FCOE_NETWORK_ALREADY_ABSENT, {}

    def __get_by_name(self, data):
        result = self.oneview_client.fcoe_networks.get_by('name', data['name'])
        return result[0] if result else None


def main():
    FcoeNetworkModule().run()


if __name__ == '__main__':
    main()
