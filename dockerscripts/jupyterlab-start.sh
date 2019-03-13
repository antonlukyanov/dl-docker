#!/usr/bin/env bash

nvidia-docker start adl-jupyterlab
docker exec -d adl-jupyterlab sudo /usr/sbin/sshd -D
