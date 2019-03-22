#!/usr/bin/env bash

prefix=$1
user=$2

if [[ "$USER" == "a.lukyanov1" ]]; then
    user=anton
    prefix=adl
elif [[ -z "$user" ]]; then
    user=$(whoami)
fi

if [[ -z "$prefix" ]]; then
    echo "You must specify a prefix (as the first argument) which is used for your image tag: \$prefix/jupyterlab:gpu."
    echo "For example, running './jupyterlab-gpu adl' will build an image with the tag adl/jupyterlab:gpu."
    exit
fi

docker build \
    -f ../dockerfiles/Deepo \
    -t $prefix/deepo:gpu \
    .

docker build \
    -f ../dockerfiles/Jupyterlab \
    --build-arg JL_PREFIX=$prefix \
    --build-arg JL_USER=$user \
    --build-arg JL_UID=$(id -u) \
    --build-arg JL_GID=$(id -g) \
    -t $prefix/jupyterlab:gpu \
    .
