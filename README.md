ansible playbook and tools to run CI performance tests on marathon


    export MARATHON_URI=http://<...>
    export ZOOKEEPER_URI="zk://<...>"  #shall end with /
    pipenv --two
    pipenv run ansible-playbook local.yml
