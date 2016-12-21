import os
import statistics
import time

import argh

import psutil
import requests

MARATHON_URL = os.environ["MARATHON_URL"]


def getMasterURL():
    r = requests.get(MARATHON_URL + "/v2/apps//master0")
    r.raise_for_status()
    data = r.json()
    for task in data['app']['tasks']:
        return "http://{}:{}/".format(task['host'], task['ports'][1])


@argh.arg('num_builds', type=int)
@argh.arg('num_workers', type=int)
def main(num_builds, num_workers, config_kind, numlines, sleep):
    os.system("python marathon.py worker {}".format(0))
    url = getMasterURL()
    print "create builds", num_builds
    start = time.time()
    for i in xrange(num_builds):
        r = requests.post(
            url + "builders/runtests/force",
            data={
                "forcescheduler": "force",
                "username": "",
                "reason": "force build",
                "branch": "",
                "revision": "",
                "repository": "",
                "project": "",
                "NUMLINES": numlines,
                "SLEEP": sleep,
                "Name": "",
            })
        r.raise_for_status()
    os.system("python marathon.py worker {}".format(num_workers))

    finished = False
    builds = []
    latencies = []
    while not finished:
        t1 = time.time()
        r = requests.get(url + "json/builders/runtests")
        r.raise_for_status()
        t2 = time.time()
        j = r.json()
        pendingBuilds = j['pendingBuilds']
        currentBuilds = j['currentBuilds']
        builds.append(len(currentBuilds))
        latencies.append(t2 - t1)
        print psutil.cpu_percent(), pendingBuilds, t2 - t1, builds[-1]
        finished = pendingBuilds == 0
        time.sleep(0.4)
    end = time.time()
    print "finished in ", end - start
    with open("marathonresults.csv", 'a') as f:
        f.write(";".join(map(str, [
            config_kind, num_builds, num_workers, numlines, sleep, end - start,
            statistics.mean(builds), statistics.mean(latencies),
            statistics.pstdev(builds), statistics.pstdev(latencies)]
        )) + "\n")

argh.dispatch_command(main)
