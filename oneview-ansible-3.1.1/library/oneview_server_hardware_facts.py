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
    from hpOneView.common import transform_list_to_dict
    from hpOneView.exceptions import HPOneViewException

    HAS_HPE_ONEVIEW = True
except ImportError:
    HAS_HPE_ONEVIEW = False

DOCUMENTATION = '''
---
module: oneview_server_hardware_facts
short_description: Retrieve facts about the OneView Server Hardwares.
description:
    - Retrieve facts about the Server Hardware from OneView.
requirements:
    - "python >= 2.7.9"
    - "hpOneView >= 3.0.0"
author: "Gustavo Hennig (@GustavoHennig)"
options:
    config:
      description:
        - Path to a .json configuration file containing the OneView client configuration.
          The configuration file is optional. If the file path is not provided, the configuration will be loaded from
          environment variables.
      required: false
    name:
      description:
        - Server Hardware name.
      required: false
    options:
      description:
        - "List with options to gather additional facts about Server Hardware related resources.
          Options allowed: bios, javaRemoteConsoleUrl, environmentalConfig, iloSsoUrl, remoteConsoleUrl,
          utilization, firmware, and firmwares."
      required: false
    params:
      description:
        - List of params to delimit, filter and sort the list of resources.
        - "params allowed:
           'start': The first item to return, using 0-based indexing.
           'count': The number of resources to return.
           'filter': A general filter/query string to narrow the list of items returned.
           'sort': The sort order of the returned data set."
      required: false
notes:
    - "A sample configuration file for the config parameter can be found at:
       https://github.com/HewlettPackard/oneview-ansible/blob/master/examples/oneview_config-rename.json"
    - "Check how to use environment variables for configuration at:
       https://github.com/HewlettPackard/oneview-ansible#environment-variables"
    - The options 'firmware' and 'firmwares' are only available for API version 300 or later.
'''

EXAMPLES = '''
- name: Gather facts about all Server Hardwares
  oneview_server_hardware_facts:
    config: "{{ config }}"
  delegate_to: localhost

- debug: var=server_hardwares


- name: Gather paginated, filtered and sorted facts about Server Hardware
  oneview_server_hardware_facts:
    config: "{{ config }}"
    params:
      start: 0
      count: 3
      sort: name:ascending
      filter: uidState='Off'
  delegate_to: localhost

- debug: msg="{{server_hardwares | map(attribute='name') | list }}"


- name: Gather facts about a Server Hardware by name
  oneview_server_hardware_facts:
    config: "{{ config }}"
    name: "172.18.6.15"
  delegate_to: localhost

- debug: var=server_hardwares


- name: Gather BIOS facts about a Server Hardware
  oneview_server_hardware_facts:
    config: "{{ config }}"
    name: "Encl1, bay 1"
    options:
      - bios
  delegate_to: localhost

- debug: var=server_hardwares
- debug: var=server_hardware_bios


- name: Gather all facts about a Server Hardware
  oneview_server_hardware_facts:
   config: "{{ config }}"
   name : "Encl1, bay 1"
   options:
       - bios                   # optional
       - javaRemoteConsoleUrl   # optional
       - environmentalConfig    # optional
       - iloSsoUrl              # optional
       - remoteConsoleUrl       # optional
       - utilization:           # optional
                fields : 'AveragePower'
                filter : ['startDate=2016-05-30T03:29:42.000Z']
                view : 'day'
       - firmware               # optional
  delegate_to: localhost

- debug: var=server_hardwares
- debug: var=server_hardware_bios
- debug: var=server_hardware_env_config
- debug: var=server_hardware_java_remote_console_url
- debug: var=server_hardware_ilo_sso_url
- debug: var=server_hardware_remote_console_url
- debug: var=server_hardware_utilization
- debug: var=server_hardware_firmware

- name: Gather facts about the Server Hardware firmware
  oneview_server_hardware_facts:
   config: "{{ config }}"
   name : "0000A66102, bay 12"
   options:
       - firmware
  delegate_to: localhost

- debug: var=server_hardware_firmware
'''

RETURN = '''
server_hardwares:
    description: Has all the OneView facts about the Server Hardware.
    returned: Always, but can be null.
    type: complex

server_hardware_bios:
    description: Has all the facts about the Server Hardware BIOS.
    returned: When requested, but can be null.
    type: complex

server_hardware_env_config:
    description: Has all the facts about the Server Hardware environmental configuration.
    returned: When requested, but can be null.
    type: complex

server_hardware_java_remote_console_url:
    description: Has the facts about the Server Hardware java remote console url.
    returned: When requested, but can be null.
    type: complex

server_hardware_ilo_sso_url:
    description: Has the facts about the Server Hardware iLO SSO url.
    returned: When requested, but can be null.
    type: complex

server_hardware_remote_console_url:
    description: Has the facts about the Server Hardware remote console url.
    returned: When requested, but can be null.
    type: complex

server_hardware_utilization:
    description: Has all the facts about the Server Hardware utilization.
    returned: When requested, but can be null.
    type: complex

server_hardware_firmware:
    description: Has all the facts about the Server Hardware firmware.
    returned: When requested, but can be null.
    type: complex

server_hardware_firmwares:
    description: Has all the facts about the firmwares inventory across all servers.
    returned: When requested, but can be null.
    type: complex
'''
HPE_ONEVIEW_SDK_REQUIRED = 'HPE OneView Python SDK is required for this module.'


class ServerHardwareFactsModule(object):
    argument_spec = dict(
        config=dict(required=False, type='str'),
        name=dict(required=False, type='str'),
        options=dict(required=False, type='list'),
        params=dict(required=False, type='dict')
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
            ansible_facts, options = {}, None

            if self.module.params.get('options'):
                options = transform_list_to_dict(self.module.params.get('options'))

            if self.module.params.get('name'):
                server_hardwares = self.oneview_client.server_hardware.get_by("name", self.module.params['name'])

                if self.module.params.get('options') and server_hardwares:
                    ansible_facts = self.gather_option_facts(options, server_hardwares[0])

            else:
                params = self.module.params.get('params') or {}
                server_hardwares = self.oneview_client.server_hardware.get_all(**params)

                if options and options.get('firmwares'):
                    ansible_facts['server_hardware_firmwares'] = self.get_all_firmwares(options)

            ansible_facts["server_hardwares"] = server_hardwares

            self.module.exit_json(changed=False,
                                  ansible_facts=ansible_facts)

        except HPOneViewException as exception:
            self.module.fail_json(msg='; '.join(str(e) for e in exception.args))

    def gather_option_facts(self, options, server_hardware):
        srv_hw_client = self.oneview_client.server_hardware
        ansible_facts = {}

        if options.get('bios'):
            ansible_facts['server_hardware_bios'] = srv_hw_client.get_bios(server_hardware['uri'])
        if options.get('environmentalConfig'):
            ansible_facts['server_hardware_env_config'] = srv_hw_client.get_environmental_configuration(
                server_hardware['uri'])
        if options.get('javaRemoteConsoleUrl'):
            ansible_facts['server_hardware_java_remote_console_url'] = srv_hw_client.get_java_remote_console_url(
                server_hardware['uri'])
        if options.get('iloSsoUrl'):
            ansible_facts['server_hardware_ilo_sso_url'] = srv_hw_client.get_ilo_sso_url(server_hardware['uri'])
        if options.get('remoteConsoleUrl'):
            ansible_facts['server_hardware_remote_console_url'] = srv_hw_client.get_remote_console_url(
                server_hardware['uri'])
        if options.get('utilization'):
            ansible_facts['server_hardware_utilization'] = self.get_utilization(server_hardware, options['utilization'])
        if options.get('firmware'):
            ansible_facts['server_hardware_firmware'] = srv_hw_client.get_firmware(server_hardware["uri"])

        return ansible_facts

    def get_all_firmwares(self, options):
        if isinstance(options['firmwares'], bool):
            params = {}
        else:
            params = options['firmwares']

        return self.oneview_client.server_hardware.get_all_firmwares(**params)

    def get_utilization(self, server_hardware, data):

        fields = view = refresh = filter = ''

        if isinstance(data, dict):
            fields = data.get('fields')
            view = data.get('view')
            refresh = data.get('refresh')
            filter = data.get('filter')

        return self.oneview_client.server_hardware.get_utilization(server_hardware['uri'],
                                                                   fields=fields,
                                                                   filter=filter,
                                                                   refresh=refresh,
                                                                   view=view)


def main():
    ServerHardwareFactsModule().run()


if __name__ == '__main__':
    main()
