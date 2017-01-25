#!/usr/bin/env python
import os
import random
import time

import argh
import requests
import yaml

MARATHON_URL = os.environ["MARATHON_URL"]


def getPgURL():
    r = requests.get(MARATHON_URL + "/v2/apps//pg0")
    r.raise_for_status()
    data = r.json()
    hostname = data['app']['tasks'][0]['host']
    port = data['app']['tasks'][0]['ports'][0]
    return "postgresql+psycopg2://buildbot:change_me@{hostname}:{port}/buildbot".format(
        hostname=hostname, port=port
    )


def getMqURL():
    r = requests.get(MARATHON_URL + "/v2/apps//mq0")
    r.raise_for_status()
    data = r.json()
    hostname = data['app']['tasks'][0]['host']
    port = data['app']['tasks'][0]['ports'][0]
    return "ws://{hostname}:{port}/ws".format(
        hostname=hostname, port=port
    )


def getInfluxdbPort():
    r = requests.get(MARATHON_URL + "/v2/apps//influxdb0")
    try:
        r.raise_for_status()
    except:
        return ('none', 12)
    data = r.json()
    hostname = data['app']['tasks'][0]['host']
    port = data['app']['tasks'][0]['ports'][1]
    return (hostname, port)


def waitQuiet():
    while True:
        r = requests.get(MARATHON_URL + "/v2/deployments")
        j = r.json()
        if len(j) == 0:
            break
        affectedApps = set()
        for app in j:
            affectedApps.update(set(app['affectedApps']))
        print affectedApps
        time.sleep(1)


def getMasterPorts():
    r = requests.get(MARATHON_URL + "/v2/apps?id=master&embed=apps.tasks")
    try:
        r.raise_for_status()
    except:
        return[(1, 2)]
    data = r.json()
    ports = []
    for app in data['apps']:
        for task in app['tasks']:
            ports.append((task['host'], task['ports'][0], task['ports'][1]))
    if not ports:
        return[('s1', '2')]
    return ports


def main(config, instances):
    dbURL = getPgURL()
    mqURL = getMqURL()
    influxdb, graphiteport = getInfluxdbPort()
    masterports = getMasterPorts()
    with open("marathon/{}.yaml".format(config)) as f:
        y = f.read()

    r = requests.get(MARATHON_URL + "/v2/apps?id={config}".format(config=config))
    for app in r.json()['apps']:
        requests.delete(MARATHON_URL + "/v2/apps/{id}?force=true".format(
            **app
        ))
    waitQuiet()
    for i in xrange(int(instances)):
        master, masterport, _ = random.choice(masterports)
        config_data = yaml.load(y.format(instanceid=i, dbURL=dbURL, mqURL=mqURL,
                                         master=master, masterport=masterport, influxdb=influxdb,
                                         graphiteport=graphiteport))
        for env in 'http_proxy', 'https_proxy', 'no_proxy':
            if env in os.environ:
                config_data.setdefault('env', {})
                config_data['env'][env] = os.environ[env]
        print config_data
        r = requests.put(MARATHON_URL + "/v2/apps/{config}{instanceid}?force=true".format(
            config=config, instanceid=i
        ), json=config_data)
        print r.content
        r.raise_for_status()
    waitQuiet()

if __name__ == "__main__":
    argh.dispatch_command(main)
