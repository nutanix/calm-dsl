# calm-dsl

## Getting Started
 - Setup: `calm init dsl`. Please fill in the right values.
 - Server status: `calm get server status`.
 - Config: `calm show config`. Check if you have the right config. By default, config is stored at `~/.calm/config.ini`. Please see `calm set config --help` for details to update config.
 - First blueprint: `calm init bp`. This will create a folder `HelloBlueprint` with all the necessary files. `HelloBlueprint/blueprint.py` is the main blueprint DSL file. Please read the comments in the beginning of the file for more details about the blueprint.
 - Compile blueprint: `calm compile bp --file HelloBlueprint/blueprint.py`. This command will print the compiled blueprint JSON.
 - Create blueprint on Calm Server: `calm create bp --file HelloBlueprint/blueprint.py --name <blueprint_name>`. Please use a unique name for `<blueprint_name>`.
 - List blueprints: `calm get bps`. You can also pass in filters like `calm get bps --name <blueprint_name>` and so on. Please look at `calm get bps --help`.
 - Describe blueprint: `calm describe bp <blueprint_name>`. It will print a summary of the blueprint.
 - Launch blueprint to create Application: `calm launch bp <blueprint_name> --app_name <app_name> -i`
 - List apps: `calm get apps`.
 - Describe app: `calm describe app <app_name>`. It will print a summary of the application and the current application state.
 - Delete app: `calm delete app <app_name>`. Hint: You can delete multiple apps using: `calm get apps -q | xargs -I {} calm delete app {}`.

## Dev Setup

MacOS:
 - Install homebrew: `/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`.
 - Install python3, git and openssl: `brew install git python3 openssl`.
 - Add path to flags: `export LDFLAGS="-L$(brew --prefix openssl)/lib"` & `export CFLAGS="-I$(brew --prefix openssl)/include"`.
 - Clone this repo and run: `make dev` from top directory.
 - Getting into virtualenv: `source venv/bin/activate`.
 - Getting out of virtualenv: `deactivate`.

Centos:
 - `make _init_centos` to setup your CentOS 7 VM for development. This will install python3 and docker.

Use:
 -  `make dev` to create/use python3 virtualenv in `$TOPDIR/venv` and setup dev environment. Activate it by calling `source venv/bin/activate`. Use `deactivate` to deactivate virtualenv.
 -  `make test` to run quick tests. `make test-all` to run all tests.
 -  `make dist` to generate a `calm.dsl` python distribution.
 -  `make docker` to build docker container. (Assumes docker client is setup on your machine)
 -  `make run` to run container.
 -  `make clean` to reset.

## Documentation

Documentation for the Calm DSL will be stored in the [docs](docs/) folder, and will continually be added to. If you're not familiar with Calm Terminology basics, please review the [Calm Terminology](docs/01-Calm-Terminology/) doc page.

## Video Links
 - Workstation Setup(https://youtu.be/uIZmHQhioZg)
 - Blueprint & App management(https://youtu.be/jb-ZllhaROs)

Code formatted by [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
