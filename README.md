# calm-dsl-engine

Calm DSL Engine describes a simpler Python 3 based DSL for writing Calm blueprints.
Look at this [example](https://github.com/ideadevice/calm-dsl-engine/blob/master/tests/next_demo/test_next_demo.py) to see a blueprint in action.

## Dev Setup

Pre-Reqs for Mac:
 - Get python3 using brew - `brew install python3`
 - Install [Docker for Mac](https://hub.docker.com/editions/community/docker-ce-desktop-mac)

Pre-Reqs for Centos:
 - `make _init_centos` to setup your CentOS 7 VM for development. This will install python3 and docker.

Use:
 - `make dev` to create/use python3 virtualenv in `$TOPDIR/venv` and setup dev environment. Activate it by calling `source venv/bin/activate`. Use `deactivate` to deactivate virtualenv.
 - `make test` to run the test cases.
 - `make dist` to generate a `calm.dsl` python distribution.
 - `make gui` to install jupyter notebook and extensions in your virtualenv.
 - `make docker` to build docker container. (Assumes docker client is setup on your machine)
 - `make run` to run container.
 - `make clean` to reset.

Code formatted by [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


## CLI Usage

Point the CLI to your Calm setup by using a config file, or command line args.

### Config file

By default, the CLI looks for this information in `~/.calm/server/config.ini`.<br/>
You can instruct it to look elsewhere by using the `--config` option to point to your config file:<br/>
`calm --config=/home/my_dir/config.ini get bps`
An example config is given at `server/config.ini`.

### Config overrides
You can override any setup details by passing them in explicitly:<br/>
`calm --ip=10.20.4.35 --port=9220 --username=custom_user --password=something ...[the rest of your command]`

## Reference

 - [Doc](https://docs.google.com/document/d/1SVTDISGy-1gZdeSOMyONON4WP6iFpZGJkdVkB_lEeZs/edit)
