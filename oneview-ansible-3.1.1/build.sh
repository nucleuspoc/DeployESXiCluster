#!/bin/bash
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

COLOR_START="[01;34m"
COLOR_SUCCESS="\e[32m"
COLOR_FAILURE="\e[31m"
COLOR_END="[00m"

exit_code_doc_generation=0
exit_code_build_oneview_ansible=0
exit_code_module_validation=0
exit_code_playbook_validation=0
exit_code_tests=0
exit_code_flake8=0
exit_code_coveralls=0

# Change current path
echo "Changing current directory to: ${BASH_SOURCE%/*}"
cd ${BASH_SOURCE%/*}
export ANSIBLE_LIBRARY=library

# Checks PYTHON_SDK
if [ -z ${PYTHON_SDK+x} ]; then
  export PYTHON_SDK=../python-hpOneView:dependencies/python-hpICsp
fi

export PYTHONPATH=$PYTHON_SDK:$ANSIBLE_LIBRARY:$PYTHONPATH

print_summary () {
  if [ $2 -eq 0 ]; then
    echo -e "  ${COLOR_SUCCESS}$1: ok${COLOR_END}"
  else
    echo -e "  ${COLOR_FAILURE}$1: failed${COLOR_END}"
    exit_code_build_oneview_ansible=$((${exit_code_build_oneview_ansible}+1))
  fi
}

validate_modules () {
  if hash ansible-validate-modules 2>/dev/null; then
    while read -r line
    do
      if [[ "$line" =~ "GPLv3" ]]; then
        echo "IGNORED ERROR: GPLv3 license header not found"
      else
        if [[ "$line" =~ "ERROR:" || "$line" =~ "IGNORE:" ]]; then
          exit_code_module_validation=1
        fi
        echo "$line"
      fi
    done < <(ansible-validate-modules library)
  else
    echo "ERROR: ansible-validate-modules is not installed."
    exit_code_module_validation=1
  fi
}

echo -e "\n${COLOR_START}Validating modules${COLOR_END}"
validate_modules

echo -e "\n${COLOR_START}Validating playbooks${COLOR_END}"
ansible-playbook -i "localhost," --syntax-check examples/*.yml
exit_code_playbook_validation=$?

echo -e "\n${COLOR_START}Running tests${COLOR_END}"
python -m unittest discover
exit_code_tests=$?

echo -e "\n${COLOR_START}Running flake8${COLOR_END}"
if hash flake8 2>/dev/null; then
  flake8 library test --max-line-length=120 --ignore=F403,F405
  exit_code_flake8=$?
else
  echo "ERROR:flake8 is not installed."
  exit_code_flake8=1
fi

#Documentation is generated only in local builds
if [ -z "$TRAVIS" ]; then
  echo -e "\n${COLOR_START}Generating markdown documentation${COLOR_END}"
  build-doc/run-doc-generation.sh
  exit_code_doc_generation=$?

#Coveralls runs only when Travis is running the build
else  
  echo -e "\n${COLOR_START}Running Coveralls${COLOR_END}"
  coverage run --source=library/ -m unittest discover
  coveralls
  exit_code_coveralls=$?
fi

echo -e "\n=== Summary =========================="
print_summary "Modules validation" ${exit_code_module_validation}
print_summary "Playboks validation" ${exit_code_playbook_validation}
print_summary "Unit tests" ${exit_code_tests}
print_summary "Flake8" ${exit_code_flake8}
print_summary "Doc Generation" ${exit_code_doc_generation}
print_summary "Coveralls" ${exit_code_coveralls}

echo "Done. Your build exited with ${exit_code_build_oneview_ansible}."
exit ${exit_code_build_oneview_ansible}
