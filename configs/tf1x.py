#
# Build configuration
#

# Base image won't be built if set to None.
DOCKERFILE_BASE = 'Deepo-py37-cu10'
DOCKERFILE_LAB = 'Lab-tf1x'

# Prefixes and suffixes for automatic names generation.
IMAGE_PREFIX = 'dld'

# Resulting names after build. Automatically generated if set to None.
# {IMAGE_PREFIX}/deepo-{BASE_IMAGE_SUFFIX}:gpu
BASE_IMAGE_NAME = None
BASE_IMAGE_SUFFIX = None

# {IMAGE_PREFIX}/deepo-{LAB_IMAGE_SUFFIX}:gpu
LAB_IMAGE_NAME = None
LAB_IMAGE_SUFFIX = 'tf1x'
LAB_CONTAINER_NAME = None

# This user will be created when running container.
IMAGE_USER = 'master'

#
# Running container configuration
#

# Automatically generated (/workspace/projects) if set to None.
NOTEBOOK_DIR = None
# HOST_DIR:CONTAINER_DIR
MOUNT = '$HOME/projects:/workspace/projects'
# HOST_PORT:CONTAINER_PORT
JUPYTERLAB_PORT = '9000:8888'
TENSORBOARD_PORT = '9001:6006'
SSHD_PORT = '9002:22'
HOSTNAME = 'dl-server'
