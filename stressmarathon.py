import os
import statistics
import time

import argh
import psutil
import requests

MARATHON_URL = os.environ["MARATHON_URL"]


def getMasterURL():
    r = requests.get(MARATHON_URL + "/v2/apps/buildbot")
    r.raise_for_status()
    data = r.json()
    for task in data['app']['tasks']:
        return "http://{}:{}/".format(task['host'], task['ports'][1])


def waitQuiet():
    while True:
        r = requests.get(MARATHON_URL + "/v2/deployments")
        j = r.json()
        if len(j) == 0:
            break
        affectedApps = set()
        for app in j:
            affectedApps.update(set(app['affectedApps']))
        time.sleep(1)


@argh.arg('num_builds', type=int)
@argh.arg('num_workers', type=int)
def main(num_builds, num_workers, config_kind, numlines, sleep):
    url = getMasterURL()
    print "stop workers"
    requests.put(MARATHON_URL + "/v2/apps/worker?force=True", json={"instances": 0})
    waitQuiet()
    print "create {} build".format(num_builds)
    start = time.time()
    for i in xrange(num_builds):
        r = requests.post(
            url + "api/v2/forceschedulers/force",
            json={"id": 1, "jsonrpc": "2.0", "method": "force", "params": {
                "builderid": "1", "username": "", "reason": "force build",
                "project": "", "repository": "", "branch": "", "revision": "",
                "NUMLINES": str(numlines),
                "SLEEP": str(sleep)}})
        r.raise_for_status()
    print "create {} workers".format(num_workers)
    requests.put(MARATHON_URL + "/v2/apps/worker?force=True", json={"instances": num_workers})

    finished = False
    builds = []
    latencies = []
    while not finished:
        t1 = time.time()
        r = requests.get(url + "api/v2/buildrequests?complete=0")
        try:
           r.raise_for_status()
        except Exception as e:
           time.sleep(1)
           print e
           continue
        brs = r.json()['buildrequests']
        t2 = time.time()
        r = requests.get(url + "api/v2/builds?complete=0")
        try:
            r.raise_for_status()
        except Exception as e:
           time.sleep(1)
           print e
           continue
        builds.append(len(r.json()['builds']))
        latencies.append(t2 - t1)
        print len(brs), t2 - t1, builds[-1]
        finished = not brs
        time.sleep(0.4)
        end = time.time()
        if end - start > 1000:
            finished = True  # timeout
            os.system("./restart.sh")
    print "finished in ", end - start
    with open("marathonresults.csv", 'a') as f:
        f.write(";".join(map(str, [
            config_kind, num_builds, num_workers, numlines, sleep, end - start,
            statistics.mean(builds), statistics.mean(latencies),
            statistics.pstdev(builds), statistics.pstdev(latencies)]
        )) + "\n")
argh.dispatch_command(main)
