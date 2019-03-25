#!/usr/bin/env python3

import os
from os.path import join
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
    return [x.replace('.sh', '') for x in os.listdir(join('configs')) if x.endswith('.py')]


def process_config(config):
    whoami = run('whoami', stdout=subprocess.PIPE).stdout.strip() or ''

    config.DEEPO_IMAGE_NAME = config.DEEPO_IMAGE_NAME or \
        f'{config.IMAGE_PREFIX}/deepo-{config.IMAGE_SUFFIX}:gpu'

    config.CONTAINER_PREFIX = whoami if whoami != 'a.lukyanov1' else 'adl'

    config.LAB_IMAGE_NAME = config.LAB_IMAGE_NAME or \
        f'{config.IMAGE_PREFIX}/lab-{config.IMAGE_SUFFIX}:gpu'

    config.LAB_CONTAINER_NAME = config.LAB_CONTAINER_NAME or \
        f'{config.CONTAINER_PREFIX}-lab-{config.IMAGE_SUFFIX}'

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

    parser_build = parser_cmd.add_parser('build', aliases=['b'])
    parser_run = parser_cmd.add_parser('run', aliases=['r'])
    parser_rmc = parser_cmd.add_parser('rmc')
    parser_rmi = parser_cmd.add_parser('rmi')
    parser_start = parser_cmd.add_parser('start')
    parser_stop = parser_cmd.add_parser('stop')
    parser_info = parser_cmd.add_parser('info')

    return parser.parse_args()


class Command:
    def __init__(self, config, dry_run=False):
        self.config = config
        self.dry_run = dry_run

    def exec(self, cmd):
        cmd = cmd.strip()
        log(f'running:\n{cmd}')
        if not self.dry_run:
            run(cmd)
        log('finished')

    def build(self):
        cfg = self.config

        if cfg.DOCKERFILE_BASE:
            self.exec(f'''
docker build \\
    -f dockerfiles/{cfg.DOCKERFILE_BASE} \\
    -t {cfg.DEEPO_IMAGE_NAME} \\
    dockercontext
            ''')

        self.exec(f'''
docker build \\
    -f dockerfiles/Lab \\
    --build-arg DLD_DEEPO={cfg.DEEPO_IMAGE_NAME} \\
    --build-arg DLD_USER={cfg.IMAGE_USER} \\
    -t {cfg.LAB_IMAGE_NAME} \\
    dockercontext
        ''')

    def run(self):
        cfg = self.config
        self.exec(f'''
nvidia-docker run \
    -d \
    -e DLD_UID=$(id -u) \
    -e DLD_GID=$(id -u) \
    --hostname dgx1 \
    --name {cfg.LAB_CONTAINER_NAME} \
    -v {cfg.MOUNT} \
    -p 8889:8888 \
    -p 8890:22 \
    -p 8899:6006 \
    --ipc host \
    {cfg.LAB_IMAGE_NAME} \
    jupyter lab \
        --ip 0.0.0.0 \
        --allow-root \
        --no-browser \
        --notebook-dir={cfg.NOTEBOOK_DIR} \
        --LabApp.token=dgxtoken

docker exec -d {cfg.LAB_CONTAINER_NAME} sudo /usr/sbin/sshd -D\
        ''')

    def start(self):
        cfg = self.config
        self.exec(f'''
nvidia-docker start {cfg.LAB_CONTAINER_NAME}
docker exec -d {cfg.LAB_CONTAINER_NAME} sudo /usr/sbin/sshd -D
        ''')

    def stop(self):
        self.exec(f'docker stop {self.config.LAB_CONTAINER_NAME}')

    def rmc(self):
        self.exec(f'docker rm {self.config.LAB_CONTAINER_NAME}')

    def rmi(self):
        cfg = self.config
        self.exec(f'''
docker rmi ${cfg.LAB_IMAGE_NAME}
docker rmi ${cfg.DEEPO_IMAGE_NAME}
        ''')

    def info(self):
        cfg = self.config
        print(f'''
Deepo image: {cfg.DEEPO_IMAGE_NAME}
Lab image: {cfg.LAB_IMAGE_NAME}
Lab container: {cfg.LAB_CONTAINER_NAME}
Mount: {cfg.MOUNT}
Notebook dir: {cfg.NOTEBOOK_DIR}
        '''.strip())


def main(args):
    cmd = args.command
    cmdo = Command(process_config(importlib.import_module('configs.' + args.config)), args.dry_run)
    if cmd in ('build', 'b'):
        cmdo.build()
    elif cmd in ('run', 'r'):
        cmdo.run()
    elif cmd == 'start':
        cmdo.start()
    elif cmd == 'stop':
        cmdo.stop()
    elif cmd == 'rmc':
        cmdo.rmc()
    elif cmd == 'info':
        cmdo.info()


if __name__ == '__main__':
    main(parse_args())
