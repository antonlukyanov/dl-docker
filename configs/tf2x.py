#
# Build configuration
#

# Base image won't be built if set to None.
DOCKERFILE_BASE = 'Deepo-py37-cu10'
DOCKERFILE_LAB = 'Lab-tf2x'

IMAGE_PREFIX = 'dld'

BASE_IMAGE_NAME = None
BASE_IMAGE_SUFFIX = None

LAB_IMAGE_NAME = None
LAB_IMAGE_SUFFIX = 'tf2x'
LAB_CONTAINER_NAME = None

IMAGE_USER = 'master'

#
# Running container configuration
#

NOTEBOOK_DIR = None
MOUNT = '$HOME/projects:/workspace/projects'
SSHD_PORT = '8890:22'
JUPYTERLAB_PORT = '8889:8888'
TENSORBOARD_PORT = '8899:6006'
