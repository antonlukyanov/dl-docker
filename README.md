# Deep learning image based on deepo

If you work on a server where you do not have normal root access, then running docker containers with root user might become a problem: files created by container will be saved with root owner and permissions. You will not be able to edit your files. Also running containers with correctly configured users lets you easily monitor which user uses computational resources. This repository contains a few images along with the collection of scripts which allow you to run containers with correct user permissions from a collection of base images in a multiuser environment.

## Quick start

- `./dldocker.py build` if image hasn't been built
- `./dldocker.py run-jl --autoports` to run jupyterlab and sshd in detached mode with automatically selected ports
- `./dldocker.py run-it-rm --mountpoint /host/dir:/container/dir bash` to run command in a new unnamed container and delete container when it stops

When user runs a container, a new `master` user is automatically created inside the container and associated with the host user. It is also possible and quite easy to execute a command inside running container with `./dldocker.py execute python3`, which will be executed under correct user and permissions.

## How it works

The main idea is that there is a base image and main images based on former. Building images and running containers is based on configuration files which specify what image to use and how to name things (image, containers etc).

Currently this repository contains two images (both images come with configured jupyterlab and sshd):

- `Lab-tf1x` with tensorflow 1.x
- `Lab-tf2x` with nightly build of tensorflow 2

It is also possible to specify base image from docker hub. Example configuration:

```python
BASE_IMAGE_NAME = 'ubuntu:18.04'
LAB_DOCKERFILE = 'Lab-tf1x'
LAB_IMAGE_SUFFIX = '-ubuntu-tf1x'
```

## Main commands

Note that `dldocker.py` accepts `--config` option where you specify configuration file from `configs` folder. Its default value is `tf1x` configuration with tensorflow 1.x. Also every command accepts `-d` flag for dry run.

- `build`: builds base and main image based on specified configuration. Working directory is `/home/master`.
- `run-jl`: creates and runs a new detached container with preconfigured jupyterlab and sshd (login/password is master/master) which can be used for remote python configuration in PyCharm. `$HOME/projects` is mounted to `/workspace/projects` and notebooks are served from `/workspace/projects` folder.
- `start`: starts stopped container created with `run-jl`.
- `stop`: stops the container created with `run-jl`.
- `run-it-rm`: interactively runs specified command in a new container and deletes container when it stops.
- `exec`: executes specified command in running container.

Run `dldocker.py -h` for more detailed information.
