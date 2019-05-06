#!/usr/bin/env bash

echo "Starting as user $DLD_USER with UID=$DLD_UID"

groupadd -r -g ${DLD_GID} ${DLD_USER}
useradd -r -u ${DLD_UID} --create-home -g ${DLD_USER} -s /bin/bash ${DLD_USER}
echo "${DLD_USER}:${DLD_USER}" | chpasswd
chown -R ${DLD_UID}:${DLD_GID} /home/${DLD_USER}
sudo -H -u ${DLD_USER} "$@"
