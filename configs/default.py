#
# Build configuration
#

# Base image won't be built if set to None.
DOCKERFILE_BASE = 'Deepo-py37-cu10'
DOCKERFILE_LAB = 'Lab-tf1x'

# Resulting names after build. Automatically generated if set to None.
DEEPO_IMAGE_NAME = None
LAB_IMAGE_NAME = None
LAB_CONTAINER_NAME = None

# Prefixes and suffixes for automatic names generation.
IMAGE_PREFIX = 'dld'
IMAGE_SUFFIX = 'tf2x'
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
SSHD_PORT = '8890:22'
JUPYTERLAB_PORT = '8889:8888'
TENSORBOARD_PORT = '8899:6006'
