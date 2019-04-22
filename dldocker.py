#!/usr/bin/env python3

import os
from os.path import join
import re
import importlib
import argparse
import subprocess
from datetime import datetime
from functools import partial


run = partial(subprocess.run, shell=True, encoding='utf-8')


def log(msg, file=None, time_prefix=True):
    if msg:
        if time_prefix:
            msg = ('[%s]: ' % datetime.now()) + msg
        if file is not None:
            print(msg)
        print(msg, file=file)


def process_config(config):
    import configs.defaults as defaults

    # Filling defaults for missing keys.
    for k in dir(defaults):
        if not k.startswith('__') and not hasattr(config, k):
            setattr(config, k, getattr(defaults, k))

    whoami = run('whoami', stdout=subprocess.PIPE).stdout.strip() or ''

    base_image_suffix = config.BASE_IMAGE_SUFFIX or ''

    config.BASE_IMAGE_NAME = config.BASE_IMAGE_NAME or \
        f'{config.IMAGE_PREFIX}/base{base_image_suffix}:gpu'

    config.LAB_CONTAINER_PREFIX = config.LAB_CONTAINER_PREFIX \
        if config.LAB_CONTAINER_PREFIX \
        else whoami + '-' if whoami != 'a.lukyanov1' else 'adl-'

    lab_image_suffix = config.LAB_IMAGE_SUFFIX or ''

    config.LAB_IMAGE_NAME = config.LAB_IMAGE_NAME or \
        f'{config.IMAGE_PREFIX}/lab{lab_image_suffix}:gpu'

    config.LAB_CONTAINER_NAME = config.LAB_CONTAINER_NAME or \
        f'{config.LAB_CONTAINER_PREFIX}lab{lab_image_suffix}'

    config.NOTEBOOK_DIR = config.NOTEBOOK_DIR or \
        '/workspace/projects'

    config.MOUNTPOINT = config.MOUNTPOINT or \
        '$HOME/projects:/workspace/projects'

    config.SSHD_PORT = config.SSHD_PORT or \
        '8890:22'

    config.JUPYTERLAB_PORT = config.JUPYTERLAB_PORT or \
        '8889:8888'

    config.TENSORBOARD_PORT = config.TENSORBOARD_PORT or \
        '8899:6006'

    config.HOSTNAME = config.HOSTNAME or \
        'dl-server'

    return config


def parse_args():
    configs = [x.replace('.py', '') for x in os.listdir(join('configs')) if x.endswith('.py') and x != 'defaults.py']

    parser = argparse.ArgumentParser(
        description='Main script for building and running deep learning images and containers.'
    )
    parser.add_argument(
        '-c',
        '--config',
        help='Configuration contaning image tag, container name and build configuration.',
        default='tf1x',
        choices=configs
    )
    parser.add_argument(
        '-d',
        '--dry-run',
        help='Dry run.',
        action='store_true'
    )
    parser.add_argument(
        '-a',
        '--autoports',
        help='Select ports automatically.',
        action='store_true'
    )

    # TODO: skip building of a base image.

    parser_cmd = parser.add_subparsers(dest='command', title='command')
    parser_cmd.required = True

    parser_build = parser_cmd.add_parser(
        'build',
        help='Builds image.'
    )
    parser_run_jl = parser_cmd.add_parser(
        'run-jl',
        help='Runs a new container and starts jupyterlab with sshd.'
    )
    parser_run_jl.add_argument(
        '--mountpoint',
        help='Container mount point in format host_path:container_path.',
    )
    parser_run_jl.add_argument(
        '--notebook-dir',
        help='Path to notebooks directory inside container.',
    )
    parser_run_it_rm = parser_cmd.add_parser(
        'run-it-rm',
        help='Interactively runs specified command in a new container and then deletes container.'
    )
    parser_run_it_rm.add_argument(
        '--mountpoint',
        help='Container mount point in format host_path:container_path.',
    )
    parser_run_it_rm.add_argument(
        'container_command',
        nargs='?'
    )
    parser_rmc = parser_cmd.add_parser(
        'rmc',
        help='Removes container.'
    )
    parser_rmi = parser_cmd.add_parser(
        'rmi',
        help='Removes image.'
    )
    parser_start = parser_cmd.add_parser(
        'start',
        help='Starts existing container.'
    )
    parser_stop = parser_cmd.add_parser(
        'stop',
        help='Stops running container.'
    )
    parser_exec = parser_cmd.add_parser(
        'exec',
        help='Executes command in a running container. Default command is bash.'
    )
    parser_exec.add_argument(
        'container_command',
        nargs='?'
    )
    parser_info = parser_cmd.add_parser(
        'info',
        help='Prints configuration summary.'
    )

    return parser.parse_args()


class Command:
    regex = re.compile(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:([0-9]+)->')

    def __init__(self, config, dry_run=False):
        self.config = config
        self.dry_run = dry_run

    def _run(self, cmd):
        cmd = cmd.strip()
        log(f'running:\n{cmd}')
        if not self.dry_run:
            run(cmd)
        log('finished')

    def _taken_ports(self):
        taken_ports = set()
        ps = run('docker ps --format \'{{.Names}} {{.Ports}}\'', stdout=subprocess.PIPE)
        if ps.stdout:
            ps = ps.stdout.strip()
            for line in ps.splitlines():
                if line:
                    taken_ports.update(self.regex.findall(line))
        return taken_ports

    def _guess_ports(self):
        start_from = max(9000, int(sorted(self._taken_ports())[-1]))
        return list(map(str, range(start_from + 1, start_from + 4)))

    def _conflicting_ports(self, ports=None):
        if not ports:
            ports = [self.config.SSHD_PORT, self.config.JUPYTERLAB_PORT, self.config.TENSORBOARD_PORT]
        conflicting_ports = []
        taken_ports = self._taken_ports()
        for port in ports:
            port = port.split(':')[0]
            if port in taken_ports:
                conflicting_ports.append(port)
        return conflicting_ports

    def _check_ports(self, ports=None):
        ports = self._conflicting_ports(ports)
        if ports:
            raise RuntimeError(f'Following ports are taken: {ports}')

    def _get_ports(self, autoports, check=True):
        cfg = self.config
        if not autoports:
            if check:
                self._check_ports()
            return cfg.JUPYTERLAB_PORT, cfg.TENSORBOARD_PORT, cfg.SSHD_PORT
        else:
            jl_port, tb_port, sshd_port = self._guess_ports()
            return f'{jl_port}:8888', f'{tb_port}:6006', f'{sshd_port}:22'

    def build(self):
        cfg = self.config

        if cfg.BASE_DOCKERFILE:
            self._run(f'''
docker build \\
    -f dockerfiles/{cfg.BASE_DOCKERFILE} \\
    -t {cfg.BASE_IMAGE_NAME} \\
    dockercontext
            ''')

        self._run(f'''
docker build \\
    -f dockerfiles/{cfg.LAB_DOCKERFILE} \\
    --build-arg DLD_BASE={cfg.BASE_IMAGE_NAME} \\
    --build-arg DLD_USER={cfg.IMAGE_USER} \\
    -t {cfg.LAB_IMAGE_NAME} \\
    dockercontext
        ''')

    def run_jl(self, autoports=False, mountpoint=None, notebook_dir=None):
        cfg = self.config
        jl_port, tb_port, sshd_port = self._get_ports(autoports)
        mountpoint = mountpoint or cfg.MOUNTPOINT
        notebook_dir = notebook_dir or cfg.NOTEBOOK_DIR
        self._run(f'''
nvidia-docker run \\
    -d \\
    -e DLD_UID=$(id -u) \\
    -e DLD_GID=$(id -g) \\
    --hostname {cfg.HOSTNAME} \\
    --name {cfg.LAB_CONTAINER_NAME} \\
    -v {mountpoint} \\
    -p {jl_port} \\
    -p {tb_port} \\
    -p {sshd_port} \\
    --ipc host \\
    {cfg.LAB_IMAGE_NAME} \\
    jupyter lab \\
        --ip 0.0.0.0 \\
        --no-browser \\
        --notebook-dir={notebook_dir} \\
        --LabApp.token=dlservertoken
docker exec -d {cfg.LAB_CONTAINER_NAME} /usr/sbin/sshd -D
        ''')

    def run_it_rm(self, command=None, mountpoint=None):
        cfg = self.config
        mountpoint = mountpoint or cfg.MOUNTPOINT
        self._run(f'''
nvidia-docker run \\
    -it \\
    --rm \\
    -e DLD_UID=$(id -u) \\
    -e DLD_GID=$(id -g) \\
    --hostname {cfg.HOSTNAME} \\
    -v {mountpoint} \\
    --ipc host \\
    {cfg.LAB_IMAGE_NAME} \\
    {command or "bash"}
        ''')

    def start(self):
        cfg = self.config
        self._run(f'''
nvidia-docker start {cfg.LAB_CONTAINER_NAME}
docker exec -d {cfg.LAB_CONTAINER_NAME} sudo /usr/sbin/sshd -D
        ''')

    def stop(self):
        self._run(f'docker stop {self.config.LAB_CONTAINER_NAME}')

    def rmc(self):
        self._run(f'docker rm {self.config.LAB_CONTAINER_NAME}')

    def rmi(self):
        self._run(f'docker rmi {self.config.LAB_IMAGE_NAME}')

    def info(self, autoports=False):
        cfg = self.config
        jl_port, tb_port, sshd_port = self._get_ports(autoports, check=False)
        print(f'''
Base image: {cfg.BASE_IMAGE_NAME}
Lab image: {cfg.LAB_IMAGE_NAME}
Lab container: {cfg.LAB_CONTAINER_NAME}
Mountpoint: {cfg.MOUNTPOINT}
Notebook dir: {cfg.NOTEBOOK_DIR}
SSHD ports: {sshd_port}
Jupyterlab ports: {jl_port}
Tensorboard ports: {tb_port}
Conflicting ports: {', '.join(self._conflicting_ports([jl_port, tb_port, sshd_port])) or '[]'}
Taken ports: {', '.join(sorted(list(self._taken_ports())))}
        '''.strip())

    def exec(self, command=None):
        run(f'docker exec -it {self.config.LAB_CONTAINER_NAME} sudo -u master {command or "bash"}')


def main(args):
    cmd = args.command
    cmdo = Command(process_config(importlib.import_module('configs.' + args.config)), args.dry_run)
    if cmd == 'build':
        cmdo.build()
    elif cmd == 'run-jl':
        cmdo.run_jl(args.autoports, args.mountpoint, args.notebook_dir)
    elif cmd == 'run-it-rm':
        cmdo.run_it_rm(args.container_command, args.mountpoint)
    elif cmd == 'start':
        cmdo.start()
    elif cmd == 'stop':
        cmdo.stop()
    elif cmd == 'rmc':
        cmdo.rmc()
    elif cmd == 'rmi':
        cmdo.rmi()
    elif cmd == 'exec':
        cmdo.exec(args.container_command)
    elif cmd == 'info':
        cmdo.info(args.autoports)


if __name__ == '__main__':
    main(parse_args())
