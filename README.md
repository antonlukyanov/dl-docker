# Deep learning image based on deepo

If you work on a server where you do not have normal root access, then running docker containers with root user might become a problem: files created by container will be saved with root owner and permissions. You will not be able to edit your files. Also running containers with correctly configured users lets you easily monitor which user uses computational resources. This repository contains a few images along with the collection of scripts which allow you to run containers with correct user permissions from one image in a multiuser environment.

## How it works

The main idea is that there is a (fat) base image and (lightweight) main images based on those. Building images and running containers is based on configuration files which specify what image to use and how to name things (image, containers etc).

Currently this repository contains two images:

- `Lab-tf1x` with tensorflow 1.x
- `Lab-tf2x` with nightly build of tensorflow 2

Both images come with configured jupyterlab and sshd.

## Quick start

- `./dldocker.py build` if image hasn't been built
- `./dldocker.py run-jl --autoports` to run jupyterlab and sshd in detached mode with automatically selected ports

When user runs the container, a new `master` user is automatically created inside new container and associated with the host user. It is also possible and quite easy to execute a command inside running container with `./dldocker.py execute python3`, which will be executed under correct user and permissions.

## Main commands

Note that `dldocker.py` accepts `--config` option which can specify configuration file from `configs` folder. Its default value is `tf1x` configuration with tensorflow 1.x. Also every command accepts `-d` flag for dry run.

- `build`: builds base and main image based on specified configuration. Working directory is `/home/master`.
- `run-jl`: creates and runs a new detached container with preconfigured jupyterlab and sshd (login/password is master/master). `$HOME/projects` is mounted to `/workspace/projects` and notebooks are served from `/workspace/projects` folder.
- `run-it`: interactively runs specified command in a new container.
- `exec`: executes specified command in running container.
- `start`: starts stopped container.
- `stop`: stops the container.

Run `dldocker.py -h` for more detailed information.
