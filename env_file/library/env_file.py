#!/usr/bin/python
# Copyright (c) 2017 Immowelt AG, Immowelt Hamburg GmbH
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: env_file
author: Dennis Kribl (@dkribl)
version_added: "2.5"

short_description: Manage environment file
description:
    - Set permanent environment variables
    - Currently developed for Debian, Ubuntu, RedHat, CentOS
    - Makes use of the /etc/environment file
notes:
    - Supports check mode
    - Supports diff
options:
    key:
        required: true
        aliases: ["name"]
        description:
            - unique identifier for environment value (key)
    value:
        required: false
        description:
            - defines the value for your identifier/key
    state:
        type: bool
        required: true
        choices: ["present", "absent"]
        default: present
        description:
            - if present add environment variable
            - if absent delete environment variable
    force:
        type: bool
        required: false
        default: true
        description:
            - if false dont overwrite variables with same key but different content
'''

EXAMPLES = '''
- env_file:
    name: http_proxy
    value: 127.0.0.1
    state: present

- env_file:
    key: ftp_proxy
    state: absent

'''

RETURN = '''#'''

import os
import copy
import tempfile
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import get_exception
from ansible.module_utils._text import to_text
from ansible.module_utils._text import to_bytes


ENVFILE = "/etc/environment"


def get_diff(before, after):
    before_d = {}
    for k, v in before.items():
        before_d[k] = v.replace('"', '').replace("\n", "")

    after_d = {}
    for k, v in after.items():
        after_d[k] = v.replace('"', '').replace("\n", "")

    diff = {'before': before_d, 'after': after_d}
    return diff


def read_environment(module):
    d = {}
    with open(ENVFILE, 'rb') as f:
        b_data = f.read().splitlines()
        for line in b_data:
            try:
                line_text = to_text(line)
            except UnicodeError:
                module.fail_json(msg="There was an error converting content of {0} as binary to text: {1}".format(ENVFILE, get_exception()))
            try:
                if '=' in line_text and not line_text.startswith('#'):
                    (k, v) = line_text.split('=')
                    d[k] = v
            except (ValueError, UnboundLocalError):
                if get_exception() == ValueError:
                    pass
                else:
                    module.fail_json(msg="There was an error reading the environment vars in {0}. Is your file corrupted?".format(ENVFILE))
    return d


def is_key_and_value_present(module, name, value, force):
    d = read_environment(module)
    if name in d:
        if d[name].replace('"', "").replace('\n', '') == value:
            return True
        else:
            if not force:
                module.fail_json(msg="There is already an environment variable called '{0}' but its content is not '{1}'. \
                If you still want to add it use the 'force: yes' parameter".format(name, value))
            else:
                return False
    else:
        return False


def is_key_present(module, name):
    d = read_environment(module)
    return True if name in d else False


def set_environment(module, name, value, force):
    if not os.path.exists(ENVFILE) and not force:
        module.fail_json(changed=False, msg="OS may not be supported because {0} is not present. \
        Use the 'force: yes' parameter to create the file".format(ENVFILE))
    elif not os.path.exists(ENVFILE) and force:
        open(ENVFILE, 'ab').close()

    if is_key_and_value_present(module, name, value, force):
        module.exit_json(changed=False)

    diff = {}
    if module._diff:
        d1 = read_environment(module)

    try:
        f = open(ENVFILE, 'ab')
        f.write(to_bytes('{0}="{1}"\n'.format(name, value)))
    except Exception:
        module.fail_json(changed=False, msg="Failed to update environment file: {0}".format(get_exception()))
    finally:
        f.close()

    if module._diff:
        d2 = read_environment(module)
        diff = get_diff(d1, d2)

    module.exit_json(changed=True, diff=diff)


def del_environment(module, name, force):
    if not os.path.exists(ENVFILE) and not force:
        module.fail_json(changed=False, msg="OS may not be supported because {0} is not present. \
        Use the 'force: yes' parameter to create the file".format(ENVFILE))
    elif not os.path.exists(ENVFILE) and force:
        open(ENVFILE, 'ab').close()

    if not is_key_present(module, name):
        module.exit_json(changed=False)

    d = read_environment(module)

    _, tmpfile = tempfile.mkstemp(dir=os.path.dirname(ENVFILE))

    if module._diff:
        d1 = copy.deepcopy(d)

    if d.get(name):
        try:
            d.pop(name, None)
        except KeyError:
            module.fail_json(msg="An undefined exception occured: {0}".format(get_exception()))

        with open(tmpfile, 'wb') as f:
            for k, v in d.items():
                f.write(to_bytes("{0}={1}\n".format(k, v)))
    try:
        module.atomic_move(tmpfile, ENVFILE)
    except IOError:
        module.fail_json(msg="Failed to update environment file: {0}".format(get_exception()))

    diff = {}
    if module._diff:
        d2 = read_environment(module)
        diff = get_diff(d1, d2)

    module.exit_json(changed=True, diff=diff)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            key=dict(aliases=['name']),
            value=dict(),
            state=dict(default='present', choices=['absent', 'present']),
            force=dict(default=True, type='bool')
        ),
        supports_check_mode=True,
        required_if=[
            ["state", "present", ["key", "value"]],
            ["state", "absent", ["key"]]
        ])
    try:
        name = module.params['name']
    except KeyError:
        name = module.params['key']

    value = module.params['value']
    state = module.params['state']
    force = module.params['force']

    if module.check_mode and state == "present":
        if not os.path.exists(ENVFILE) and not force:
            module.fail_json(changed=False, msg="OS may not be supported because {0} is not present. \
            Use the 'force: yes' parameter to create the file".format(ENVFILE))
        elif not os.path.exists(ENVFILE) and force:
            open(ENVFILE, 'ab').close()
            if is_key_and_value_present(module, name, value, force):
                os.remove(ENVFILE)
                module.exit_json(changed=False)
            else:
                os.remove(ENVFILE)
                module.exit_json(changed=True)

    elif module.check_mode and state == "absent":
        if not os.path.exists(ENVFILE) and not force:
            module.fail_json(changed=False, msg="OS may not be supported because {0} is not present. \
            Use the 'force: yes' parameter to create the file".format(ENVFILE))
        elif not os.path.exists(ENVFILE) and force:
            open(ENVFILE, 'ab').close()
            if not is_key_and_value_present(module, name, value, force):
                os.remove(ENVFILE)
                module.exit_json(changed=False)
            else:
                os.remove(ENVFILE)
                module.exit_json(changed=True)

    if state == "present":
        set_environment(module, name, value, force)
    elif state == "absent":
        del_environment(module, name, force)

    module.exit_json()

if __name__ == '__main__':
    main()
