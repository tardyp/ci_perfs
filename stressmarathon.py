import os
import socket
import statistics
import time

import argh
import requests

MARATHON_URL = os.environ["MARATHON_URL"]


def getMasterURL():
    r = requests.get(MARATHON_URL + "/v2/apps/buildbot")
    r.raise_for_status()
    data = r.json()
    for task in data['app']['tasks']:
        return "http://{}:{}/".format(task['host'], 30030)


def getInfluxPort():
    r = requests.get(MARATHON_URL + "/v2/apps/influxdb")
    r.raise_for_status()
    data = r.json()
    for task in data['app']['tasks']:
        return (task['host'], 30011)
    return None


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


def restartPgAndMaster():
    print "restarting pg"
    requests.post(MARATHON_URL + "/v2/apps/pg/restart")
    waitQuiet()
    print "restarting buildbot"
    requests.post(MARATHON_URL + "/v2/apps/buildbot/restart")
    waitQuiet()
    while True:
        url = getMasterURL()
        try:
            r = requests.get(
                url + "api/v2/forceschedulers/force")
            print r.status_code
            if r.status_code == 200:
                return
        except:
            pass
        time.sleep(1)

def sendCollectd(influx, datas):
    if influx is None:
        return
    message = ""
    for name, value in datas:
        message += 'collectd.MESOS.docker_stats.stresstest.default.gauge.stress.{} {} {}\n'.format(
            name, value, int(time.time()))
    sock = socket.socket()
    try:
        sock.connect(influx)
        sock.sendall(message)
        sock.close()
    except:
        pass


@argh.arg('num_builds', type=int)
@argh.arg('num_workers', type=int)
@argh.arg('num_masters', type=int)
def main(num_builds, num_workers, num_masters, config_kind, numlines, sleep, firstRestart=False):
    if firstRestart:
        restartPgAndMaster()

    requests.put(MARATHON_URL + "/v2/apps/buildbot?force=True", json={"instances": num_masters})
    config_kind += str(num_masters)
    waitQuiet()
    url = getMasterURL()
    influx = getInfluxPort()
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
        try:
            r = requests.get(url + "api/v2/buildrequests?complete=0")
            r.raise_for_status()
        except Exception as e:
            time.sleep(1)
            print e
            continue
        brs = r.json()['buildrequests']
        t2 = time.time()
        try:
            r = requests.get(url + "api/v2/builds?complete=0")
            r.raise_for_status()
        except Exception as e:
            time.sleep(1)
            print e
            continue
        builds.append(len(r.json()['builds']))
        latencies.append(t2 - t1)
        sendCollectd(influx, [
            ("concurrent_builds", builds[-1]),
            ("pending_buildrequests", len(brs)),
            ("www_latency", t2 - t1),
            ("num_workers", num_workers),
            ("numlines", numlines),
            ("sleep", sleep)
        ])
        print len(brs), t2 - t1, builds[-1], "\r",
        finished = not brs
        time.sleep(0.4)
        end = time.time()
        if end - start > 1000:
            finished = True  # timeout
            sendCollectd(influx, [("restarted", 1)])
            restartPgAndMaster()
        try:
            requests.delete(MARATHON_URL + "/v2/queue//worker/delay")
        except:
            pass
    print "finished in ", end - start
    requests.post("http://events.buildbot.net/events/ci_perfs", json=dict(
        config_kind=config_kind, num_builds=num_builds, num_workers=num_workers,
        numlines=numlines, sleep=sleep, time=end - start,
        mean_builds=statistics.mean(builds), mean_latencies=statistics.mean(latencies),
        pstdev_builds=statistics.pstdev(builds), pstdev_latencies=statistics.pstdev(latencies)))


argh.dispatch_command(main)
