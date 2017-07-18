#!/usr/bin/python
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
module: oneview_os_deployment_plan_facts
short_description: Retrieve facts about one or more Os Deployment Plans.
description:
    - Retrieve facts about one or more of the Os Deployment Plans from OneView.
requirements:
    - "python >= 2.7.9"
    - "hpOneView >= 3.0.0"
author:
    - Abilio Parada (@abiliogp)
    - Gustavo Hennig (@GustavoHennig)
options:
    config:
      description:
        - Path to a .json configuration file containing the OneView client configuration.
          The configuration file is optional. If the file path is not provided, the configuration will be loaded from
          environment variables.
      required: false
    name:
      description:
        - Os Deployment Plan name.
      required: false
    options:
      description:
        - "List with options to gather facts about OS Deployment Plan.
          Option allowed: osCustomAttributesForServerProfile
          The option 'osCustomAttributesForServerProfile' retrieves the list of editable OS Custom Atributes, prepared
          for Server Profile use."
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
'''

EXAMPLES = '''
- name: Gather facts about all OS Deployment Plans
  oneview_os_deployment_plan_facts:
    config: "{{ config }}"
  delegate_to: localhost
- debug: var=os_deployment_plans

- name: Gather paginated, filtered and sorted facts about OS Deployment Plans
  oneview_os_deployment_plan_facts:
    config: "{{ config }}"
    params:
      start: 0
      count: 3
      sort: name:ascending
      filter: deploymentApplianceIpv4='15.212.171.216'
  delegate_to: localhost
- debug: var=os_deployment_plans

- name: Gather facts about an OS Deployment Plan by name
  oneview_os_deployment_plan_facts:
    config: "{{ config }}"
    name: "Deployment Plan"
  delegate_to: localhost
- debug: var=os_deployment_plans

- name: Gather facts about an OS Deployment Plan by name with OS Custom Attributes option
  oneview_os_deployment_plan_facts:
    config: "{{ config }}"
    name: "Deployment Plan"
    options:
      # This option will generate an os_deployment_plan_custom_attributes facts in the Server Profile format.
      - osCustomAttributesForServerProfile
  delegate_to: localhost
- debug: var=os_deployment_plans
- debug: var=os_deployment_plan_custom_attributes
'''

RETURN = '''
os_deployment_plans:
    description: Has all the OneView facts about the Os Deployment Plans.
    returned: Always, but can be null.
    type: complex

os_deployment_plan_custom_attributes:
    description: Has the editable Custom Attribute facts of the Os Deployment Plans in the Server Profiles format.
    returned: When requested, but can be empty.
    type: complex
'''
HPE_ONEVIEW_SDK_REQUIRED = 'HPE OneView Python SDK is required for this module.'


class OsDeploymentPlanFactsModule(object):
    argument_spec = {
        "config": {"required": False, "type": 'str'},
        "name": {"required": False, "type": 'str'},
        "options": {"required": False, "type": 'list'},
        "params": {"required": False, "type": 'dict'},
    }

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
            ansible_facts = {}
            if self.module.params.get('name'):
                os_deployment_plans = self.oneview_client.os_deployment_plans.get_by('name', self.module.params['name'])

                if self.module.params.get('options') and os_deployment_plans:
                    option_facts = self._gather_option_facts(self.module.params['options'], os_deployment_plans[0])
                    ansible_facts.update(option_facts)

            else:
                params = self.module.params.get('params') or {}
                os_deployment_plans = self.oneview_client.os_deployment_plans.get_all(**params)

            ansible_facts['os_deployment_plans'] = os_deployment_plans

            self.module.exit_json(changed=False,
                                  ansible_facts=ansible_facts)

        except HPOneViewException as exception:
            self.module.fail_json(msg='; '.join(str(e) for e in exception.args))

    def _gather_option_facts(self, options, resource):
        options = transform_list_to_dict(options)

        ansible_facts = {}
        custom_attributes = []

        nic_names = []
        expected_attr_for_nic = {
            "connectionid": "",
            "dhcp": False,
            "ipv4disable": False,
            "networkuri": "",
            "constraint": "auto",
        }

        # It's just a cache to avoid iterate custom_attributes
        names_added_to_ca = {}

        if options.get('osCustomAttributesForServerProfile'):
            for item in resource['additionalParameters']:
                if item.get("caType") == "nic":
                    nic_names.append(item.get('name'))
                    continue

                if item.get("caEditable"):
                    custom_attributes.append({
                        "name": item.get('name'),
                        "value": item.get('value')
                    })
                    names_added_to_ca[item.get('name')] = item.get('value')

        for nic_name in nic_names:
            expected_attr_for_nic.pop("parameters", None)
            for ckey, cvalue in expected_attr_for_nic.iteritems():

                if ckey not in names_added_to_ca:
                    custom_attributes.append({
                        "name": nic_name + "." + ckey,
                        "value": cvalue
                    })

        ansible_facts['os_deployment_plan_custom_attributes'] = {
            "os_custom_attributes_for_server_profile": custom_attributes}

        return ansible_facts


def main():
    OsDeploymentPlanFactsModule().run()


if __name__ == '__main__':
    main()
