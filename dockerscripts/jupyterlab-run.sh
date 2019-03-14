#!/usr/bin/env bash

nvidia-docker run \
    -d \
    -u $(id -u):$(id -g) \
    --hostname dgx1 \
    --name adl-jupyterlab \
    -v $HOME/projects:/workspace/projects \
    -p 8889:8888 \
    -p 8890:22 \
    -p 8899:6006 \
    --ipc host \
    adl/jupyterlab:gpu \
    jupyter lab \
        --ip 0.0.0.0 \
        --allow-root \
        --no-browser \
        --notebook-dir=/workspace/projects \
        --LabApp.token=dgxtoken

docker exec -d adl-jupyterlab sudo /usr/sbin/sshd -D
