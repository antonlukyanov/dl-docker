#!/usr/bin/env bash

echo "Starting as user $DLD_USER with UID=$DLD_UID"

group_name=${DLD_USER}

groupadd -r -g ${DLD_GID} ${group_name}
useradd -r -u ${DLD_UID} --create-home -g ${group_name} -s /bin/bash ${DLD_USER}
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/extras/CUPTI/lib64:$LD_LIBRARY_PATH' > /home/master/.bashrc
echo "${DLD_USER}:${group_name}" | chpasswd
chown -R ${DLD_UID}:${DLD_GID} /home/${DLD_USER}
sudo -E -H -u ${DLD_USER} "$@"
