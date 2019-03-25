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


def list_configs():
    return [x.replace('.py', '') for x in os.listdir(join('configs')) if x.endswith('.py')]


def process_config(config):
    whoami = run('whoami', stdout=subprocess.PIPE).stdout.strip() or ''

    base_image_suffix = '-' + config.BASE_IMAGE_SUFFIX if config.BASE_IMAGE_SUFFIX else ''

    config.BASE_IMAGE_NAME = config.BASE_IMAGE_NAME or \
        f'{config.IMAGE_PREFIX}/base{base_image_suffix}:gpu'

    config.CONTAINER_PREFIX = whoami if whoami != 'a.lukyanov1' else 'adl'

    lab_image_suffix = '-' + config.LAB_IMAGE_SUFFIX if config.LAB_IMAGE_SUFFIX else ''

    config.LAB_IMAGE_NAME = config.LAB_IMAGE_NAME or \
        f'{config.IMAGE_PREFIX}/lab{lab_image_suffix}:gpu'

    config.LAB_CONTAINER_NAME = config.LAB_CONTAINER_NAME or \
        f'{config.CONTAINER_PREFIX}-lab{lab_image_suffix}'

    config.NOTEBOOK_DIR = config.NOTEBOOK_DIR or \
        '/workspace/projects'

    config.MOUNT = config.MOUNT or \
        '$HOME/projects:/workspace/projects'

    config.SSHD_PORT = config.SSHD_PORT or \
        '8890:22'

    config.JUPYTERLAB_PORT = config.JUPYTERLAB_PORT or \
        '8889:8888'

    config.TENSORBOARD_PORT = config.TENSORBOARD_PORT or \
        '8899:6006'

    return config


def parse_args():
    parser = argparse.ArgumentParser(
        description='Main script used for building and running deep learning images and containers.'
    )
    parser.add_argument(
        '-c',
        '--config',
        help='Configuration contaning image tag, container name and build configuration.',
        default='default',
        choices=list_configs()
    )
    parser.add_argument(
        '-d',
        '--dry-run',
        help='Dry run.',
        action='store_true'
    )

    parser_cmd = parser.add_subparsers(dest='command')
    parser_cmd.required = True

    parser_build = parser_cmd.add_parser(
        'build',
        description='Builds image.'
    )
    parser_run_jl = parser_cmd.add_parser(
        'run-jl',
        description='Runs a new container and jupyterlab with sshd.'
    )
    parser_run_it = parser_cmd.add_parser(
        'run-it',
        description='Interactively runs specified command in a new container.'
    )
    parser_run_it.add_argument(
        'container_command',
        nargs='?'
    )
    parser_rmc = parser_cmd.add_parser(
        'rmc',
        description='Removes container.'
    )
    parser_rmi = parser_cmd.add_parser(
        'rmi',
        description='Removes image.'
    )
    parser_start = parser_cmd.add_parser(
        'start',
        description='Starts existing container.'
    )
    parser_stop = parser_cmd.add_parser(
        'stop',
        description='Stops running container.'
    )
    parser_exec = parser_cmd.add_parser(
        'exec',
        description='Executes command in a running container. Default command is bash.'
    )
    parser_exec.add_argument(
        'container_command',
        nargs='?'
    )
    parser_info = parser_cmd.add_parser('info')

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
                if line and self.config.LAB_CONTAINER_NAME not in line:
                    taken_ports.update(self.regex.findall(line))
        return taken_ports

    def _conflicting_ports(self):
        conflicting_ports = []
        taken_ports = self._taken_ports()
        for port in [self.config.SSHD_PORT, self.config.JUPYTERLAB_PORT, self.config.TENSORBOARD_PORT]:
            port = port.split(':')[0]
            if port in taken_ports:
                conflicting_ports.append(port)
        return conflicting_ports

    def _check_ports(self):
        ports = self._conflicting_ports()
        if ports:
            raise RuntimeError(f'Following ports are taken: {ports}')

    def build(self):
        cfg = self.config

        if cfg.DOCKERFILE_BASE:
            self._run(f'''
docker build \\
    -f dockerfiles/{cfg.DOCKERFILE_BASE} \\
    -t {cfg.BASE_IMAGE_NAME} \\
    dockercontext
            ''')

        self._run(f'''
docker build \\
    -f dockerfiles/{cfg.DOCKERFILE_LAB} \\
    --build-arg DLD_BASE={cfg.BASE_IMAGE_NAME} \\
    --build-arg DLD_USER={cfg.IMAGE_USER} \\
    -t {cfg.LAB_IMAGE_NAME} \\
    dockercontext
        ''')

    def run_jl(self):
        cfg = self.config
        self._run(f'''
nvidia-docker run \\
    -d \\
    -e DLD_UID=$(id -u) \\
    -e DLD_GID=$(id -u) \\
    --hostname dgx1 \\
    --name {cfg.LAB_CONTAINER_NAME} \\
    -v {cfg.MOUNT} \\
    -p 8889:8888 \\
    -p 8890:22 \\
    -p 8899:6006 \\
    --ipc host \\
    {cfg.LAB_IMAGE_NAME} \\
    jupyter lab \\
        --ip 0.0.0.0 \\
        --allow-root \\
        --no-browser \\
        --notebook-dir={cfg.NOTEBOOK_DIR} \\
        --LabApp.token=dgxtoken
        ''')
        self._run(f'docker exec -d {cfg.LAB_CONTAINER_NAME} /usr/sbin/sshd -D')

    def run_it(self, command=None):
        cfg = self.config
        self._run(f'''
nvidia-docker run \\
    -it \\
    -e DLD_UID=$(id -u) \\
    -e DLD_GID=$(id -u) \\
    --hostname dgx1 \\
    --name {cfg.LAB_CONTAINER_NAME} \\
    -v {cfg.MOUNT} \\
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
        cfg = self.config
        self._run(f'''
docker rmi ${cfg.LAB_IMAGE_NAME}
docker rmi ${cfg.BASE_IMAGE_NAME}
        ''')

    def info(self):
        cfg = self.config
        print(f'''
Base image: {cfg.BASE_IMAGE_NAME}
Lab image: {cfg.LAB_IMAGE_NAME}
Lab container: {cfg.LAB_CONTAINER_NAME}
Mount: {cfg.MOUNT}
Notebook dir: {cfg.NOTEBOOK_DIR}
SSHD ports: {cfg.SSHD_PORT}
Jupyterlab ports: {cfg.JUPYTERLAB_PORT}
Tensorboard ports: {cfg.TENSORBOARD_PORT}
Conflicting ports: {self._conflicting_ports()}
Taken ports: {sorted(list(self._taken_ports()))}
        '''.strip())

    def exec(self, command=None):
        run(f'docker exec -it {self.config.LAB_CONTAINER_NAME} sudo -u master {command or "bash"}')


def main(args):
    cmd = args.command
    cmdo = Command(process_config(importlib.import_module('configs.' + args.config)), args.dry_run)
    if cmd == 'build':
        cmdo.build()
    elif cmd == 'run-jl':
        cmdo.run_jl()
    elif cmd == 'run-it':
        cmdo.run_it(args.container_command)
    elif cmd == 'start':
        cmdo.start()
    elif cmd == 'stop':
        cmdo.stop()
    elif cmd == 'rmc':
        cmdo.rmc()
    elif cmd == 'exec':
        cmdo.exec(args.container_command)
    elif cmd == 'info':
        cmdo.info()


if __name__ == '__main__':
    main(parse_args())