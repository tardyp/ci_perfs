
= ZKWorker

== A docker image which can get an id from zookeeper.

When deploying workers in Marathon, you want to only create one "worker" application, and then scale it.
How many instance is how many worker you want to connect to the master.

Problem is with Buildbot, each worker needs to be identified with unique name that the master knows in advance.
So there is a need to assign an instance number to each worker.
The only id that each instance is given is the taskid, which is not predictable.

In this image we change the buildbot.tac so that the worker first connect to zookeeper coordination server, and get an incremental number from there.
The master then has to configure enough worker0..N workers, and everything will work.
Following environment variable must be set for this to work

    WORKERNAME: "worker{zk://zookeeper:port/worker/ids/}"

== Why not using MarathonLatentWorker?

This image is made for performance testing of buildbot build creation and log gathering.
Adding the latency of on demand worker creation via marathon would add too much overhead.
