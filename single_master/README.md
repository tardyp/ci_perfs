how to run this performance test:

- in your virtualenv:

```
    pip install 'buildbot[bundle]' docker-py psycopg2
```

- make sure your user has access to docker /var/lib/docker.sock


- create pg in docker, but user /dev/shm to host the data (in memory database)

```
    docker run -v /dev/shm/pgdata:/var/lib/postgresql/data -e POSTGRES_PASSWORD=example -p 5432:5432 postgres:alpine
    buildbot upgrade-master
    buildbot start --nodaemon
```

Then trigger the compute build 
