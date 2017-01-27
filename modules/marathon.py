#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, James Earl Douglas <james@earldouglas.com>
#
# This file is part of Ansible.
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

import time
from json import dumps, loads

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


DOCUMENTATION = """
module: marathon
short_description: Deploy applications to Marathon
description:
  - Deploy applications to Marathon

options:
  marathon_uri:
    required: true
    description:
      - Base URI of the Marathon master

  app_id:
    required: true
    description:
      - The Marathon appId, used via <marathon>/v2/apps/:app_id

  app_json:
    required: true
    description:
      - The Marathon app descriptor (app.json)

author: "James Earl Douglas (james@earldouglas.com)"
"""

EXAMPLES = """
# Deploy an application to Marathon
- name: Deploy to Marathon
  marathon:
    marathon_uri: https://example.com:8080/
    app_id: myApp
    app_json: "{{ lookup('file', '/path/to/app.json') }}"
"""


def request(url, method, data, accepted_responses=(200, 201, 204)):
    global module
    try:
        response, info = fetch_url(module=module, url=url, data=data, method=method,
                                   headers={'Content-Type': 'application/json'})

        if info['status'] not in accepted_responses:
            msg = {
                "description": "request failed",
                "url": url,
                "method": method,
                "data": data,
                "info": info
            }
            module.fail_json(msg=dumps(msg))
        if response:
            body = response.read()
        else:
            return {}
        if body:
            return loads(body)
        else:
            return {}

    except Exception, e:
        msg = {
            "description": "could not {} to Marathon".format(method),
            "marathon_uri": repr(url),
            "app_json": repr(data),
            "exception": repr(e)
        }
        return module.fail_json(msg=dumps(msg))


def get(url, **kwargs):
    return request(url, method='get', data=None, **kwargs)


def put(url, data):
    return request(url, method='PUT', data=data)


def enforceInts(d):
    if not isinstance(d, dict):
        return d
    for k, v in list(d.items()):
        if k in ("servicePort", "instances", "port") and isinstance(v, str):
            d[k] = int(v)
        if k.endswith("Port"):
            d[k] = int(v)
        if isinstance(v, dict):
            d[k] = enforceInts(v)
        if isinstance(v, list):
            d[k] = [enforceInts(_) for _ in v]
    return d


def waitQuiet(MARATHON_URL):
    while True:
        r = get(MARATHON_URL + "v2/deployments")
        if len(r) == 0:
            break
        time.sleep(1)


def main():

    global module
    module = AnsibleModule(
        argument_spec=dict(
            marathon_uri=dict(required=True),
            wait_quiet=dict(default='false', type="bool"),
            app_id=dict(required=True),
            app_json=dict(required=True, type="dict"),
        ),
    )

    marathon_uri = module.params['marathon_uri']
    app_id = module.params['app_id']
    wait_quiet = module.params['wait_quiet']
    app_json = module.params['app_json']
    if not isinstance(app_json, dict):
        return module.fail_json(msg="app_json should be a dict: {}".format(app_json))
    app_json = dumps(enforceInts(app_json))

    if not marathon_uri.endswith('/'):
        marathon_uri = marathon_uri + '/'

    if wait_quiet:
        waitQuiet(marathon_uri)

    marathon_uri = marathon_uri + 'v2/apps/' + app_id
    versions_before = get(marathon_uri + "/versions", accepted_responses=(200, 404))
    ret = put(marathon_uri + '?force=true', app_json)
    versions_after = get(marathon_uri + "/versions", accepted_responses=(200, 404))
    if versions_before != versions_after:
        module.exit_json(changed=True, meta=ret)
    else:
        module.exit_json(changed=False)

main()
