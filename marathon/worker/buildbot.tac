import fnmatch
import os
import sys
import urlparse

from twisted.application import service
from twisted.internet import reactor
from twisted.python.log import FileLogObserver, ILogObserver

from buildbot_worker.bot import Worker


def getZookeperId(zk_url):
    from kazoo.client import KazooClient, KazooState
    path = urlparse.urlparse(zk_url)
    hosts = path.netloc
    dir_path = path.path
    zk = KazooClient(hosts=hosts)

    def my_listener(state):
        print("zk state:", state)
        if state in (KazooState.LOST, KazooState.SUSPENDED):
            reactor.stop()

    zk.add_listener(my_listener)
    zk.start()
    path = zk.create(dir_path, ephemeral=True, sequence=True, makepath=True)

    def shutdown():
        zk.delete(path)
        # deleting the parent path will make the id restart from 0
        if len(zk.get_children(dir_path)) == 0:
            zk.delete(dir_path)

        zk.stop()
        zk.close()
    reactor.addSystemEventTrigger("during", 'shutdown', shutdown)
    return str(int(path.split("/")[-1]))
# setup worker
basedir = os.path.abspath(os.path.dirname(__file__))
application = service.Application('buildbot-worker')


application.setComponent(ILogObserver, FileLogObserver(sys.stdout).emit)
# and worker on the same process!
buildmaster_host = os.environ.get("BUILDMASTER", 'localhost')
port = int(os.environ.get("BUILDMASTER_PORT", 9989))
numworkers = int(os.environ.get("NUMWORKER", '1'))

workername = os.environ.get("WORKERNAME", 'docker')
if "{zk:" in workername:
    zk_url = "zk:" + workername.split("{zk:")[1].split("}")[0]
    baseid = int(getZookeperId(zk_url)) * numworkers
else:
    baseid = None
passwd = os.environ.get("WORKERPASS")

# delete the password from the environ so that it is not leaked in the log
blacklist = os.environ.get("WORKER_ENVIRONMENT_BLACKLIST", "WORKERPASS").split()
for name in list(os.environ.keys()):
    for toremove in blacklist:
        if fnmatch.fnmatch(name, toremove):
            del os.environ[name]

keepalive = 600
umask = None
maxdelay = 300
allow_shutdown = None

for i in range(numworkers):
    if baseid is not None:
        _workername = workername.replace("{" + zk_url + "}", "%03d" % (baseid + i))
    else:
        _workername = workername
    print("workname:", _workername)
    _basedir = os.path.join(basedir, _workername)
    s = Worker(buildmaster_host, port, _workername, passwd, _basedir,
               keepalive, umask=umask, maxdelay=maxdelay,
               allow_shutdown=allow_shutdown)
    s.setServiceParent(application)
