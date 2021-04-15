#
# Build configuration
#

# Base image won't be built if set to None.
BASE_DOCKERFILE = 'Deepo-py38-cu10'
LAB_DOCKERFILE = 'Lab-tf2'

# Prefix for all images. Image tags will be in format {IMAGE_PREFIX}/{...}:gpu
# Uses current user name by default.
IMAGE_PREFIX = None

# Resulting names after build. Automatically generated if set to None.
# {IMAGE_PREFIX}/base{BASE_IMAGE_SUFFIX}:gpu
BASE_IMAGE_NAME = None
BASE_IMAGE_SUFFIX = None

# Final image name is automatically generated if set to None:
# LAB_IMAGE_NAME = {IMAGE_PREFIX}/lab{LAB_IMAGE_SUFFIX}:gpu
LAB_IMAGE_NAME = None
LAB_IMAGE_SUFFIX = '-tf2'

# Automatically generated if set to None.
# {LAB_CONTAINER_PREFIX}lab{LAB_CONTAINER_SUFFIX}
# E.g. running 'dldocker.py -c tf2 run-jl' will result in container name user-lab-tf2 if current user name is 'user' or
# running 'dldocker.py -c newproj run-jl' will result in container name user-lab-newproj.
LAB_CONTAINER_NAME = None
# Defaults to $(whoami)-.
LAB_CONTAINER_PREFIX = None
# Defaults to config file name.
LAB_CONTAINER_SUFFIX = None

# This user will be created when running container.
IMAGE_USER = 'master'

#
# Running container configuration
#

# Container hostname.
HOSTNAME = 'dl-server'
# Jupyterlab default folder.
NOTEBOOK_DIR = '/workspace/projects'
# HOST_DIR:CONTAINER_DIR
MOUNTPOINT = '$HOME/projects:/workspace/projects'
WORKDIR = '/workspace/projects'
# HOST_PORT:CONTAINER_PORT
JUPYTERLAB_PORT = '9000:8888'
TENSORBOARD_PORT = '9001:6006'
SSHD_PORT = '9002:22'
