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
    from hpOneView.exceptions import HPOneViewResourceNotFound

    HAS_HPE_ONEVIEW = True
except ImportError:
    HAS_HPE_ONEVIEW = False

DOCUMENTATION = '''
---
module: oneview_connection_template
short_description: Manage the OneView Connection Template resources.
description:
    - "Provides an interface to manage the Connection Template resources. Can update."
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
            - Indicates the desired state for the Connection Template resource.
              'present' will ensure data properties are compliant with OneView.
        choices: ['present']
        required: true
    data:
        description:
            - List with Connection Template properties and its associated states.
        required: true
notes:
    - "A sample configuration file for the config parameter can be found at:
       https://github.com/HewlettPackard/oneview-ansible/blob/master/examples/oneview_config-rename.json"
    - "Check how to use environment variables for configuration at:
       https://github.com/HewlettPackard/oneview-ansible#environment-variables"
'''

EXAMPLES = '''
- name: Update the Connection Template
  oneview_connection_template:
    config: "{{ config }}"
    state: present
    data:
        name: 'name1304244267-1467656930023'
        type : "connection-template"
        bandwidth :
            maximumBandwidth : 10000
            typicalBandwidth : 2000
        newName : "CT-23"
  delegate_to: localhost
'''

RETURN = '''
connection_template:
    description: Has the OneView facts about the Connection Template.
    returned: On 'present' state, but can be null.
    type: complex
'''

CONNECTION_TEMPLATE_UPDATED = 'Connection Template updated successfully.'
CONNECTION_TEMPLATE_NOT_FOUND = 'Connection Template was not found.'
CONNECTION_TEMPLATE_ALREADY_UPDATED = 'Connection Template is already updated.'
CONNECTION_TEMPLATE_MANDATORY_FIELD_MISSING = "Mandatory field was not informed: data.name"
HPE_ONEVIEW_SDK_REQUIRED = 'HPE OneView Python SDK is required for this module.'


class ConnectionTemplateModule(object):
    argument_spec = dict(
        config=dict(required=False, type='str'),
        state=dict(
            required=True,
            choices=['present']
        ),
        data=dict(required=True, type='dict')
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
        try:
            state = self.module.params['state']
            data = self.module.params['data']
            changed, msg, ansible_facts = False, '', {}

            if not data.get('name'):
                raise HPOneViewValueError(CONNECTION_TEMPLATE_MANDATORY_FIELD_MISSING)

            resource = (self.oneview_client.connection_templates.get_by("name", data['name']) or [None])[0]

            if state == 'present':
                changed, msg, ansible_facts = self.__present(data, resource)

            self.module.exit_json(changed=changed,
                                  msg=msg,
                                  ansible_facts=ansible_facts)

        except HPOneViewException as exception:
            self.module.fail_json(msg='; '.join(str(e) for e in exception.args))

    def __present(self, data, resource):

        changed = False
        msg = ''

        if not resource:
            raise HPOneViewResourceNotFound(CONNECTION_TEMPLATE_NOT_FOUND)
        else:
            if 'newName' in data:
                data['name'] = data.pop('newName')

            merged_data = resource.copy()
            merged_data.update(data)

            if not resource_compare(resource, merged_data):
                # update resource
                changed = True
                resource = self.oneview_client.connection_templates.update(merged_data)
                msg = CONNECTION_TEMPLATE_UPDATED
            else:
                msg = CONNECTION_TEMPLATE_ALREADY_UPDATED

        return changed, msg, dict(connection_template=resource)


def main():
    ConnectionTemplateModule().run()


if __name__ == '__main__':
    main()
