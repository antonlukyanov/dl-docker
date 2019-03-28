#
# Build configuration
#

# Base image won't be built if set to None.
BASE_DOCKERFILE = 'Deepo-py37-cu10'
LAB_DOCKERFILE = 'Lab-tf1x'

# Prefix for all images. Image tags will be in format {IMAGE_PREFIX}/{...}:gpu
IMAGE_PREFIX = 'dld'

# Resulting names after build. Automatically generated if set to None.
# {IMAGE_PREFIX}/deepo{BASE_IMAGE_SUFFIX}:gpu
BASE_IMAGE_NAME = None
BASE_IMAGE_SUFFIX = None

# {IMAGE_PREFIX}/deepo{LAB_IMAGE_SUFFIX}:gpu
LAB_IMAGE_NAME = None
LAB_IMAGE_SUFFIX = '-tf1x'
# Automatically generated if set to None.
# {LAB_CONTAINER_PREFIX}lab{LAB_IMAGE_SUFFIX}
LAB_CONTAINER_NAME = None
# Defaults to $(whoami)-.
LAB_CONTAINER_PREFIX = None

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
MOUNT = '$HOME/projects:/workspace/projects'
# HOST_PORT:CONTAINER_PORT
JUPYTERLAB_PORT = '9000:8888'
TENSORBOARD_PORT = '9001:6006'
SSHD_PORT = '9002:22'
