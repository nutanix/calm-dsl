[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

![Build](https://github.com/nutanix/calm-dsl/workflows/Setup%20&%20build%20calm-dsl/badge.svg)

# calm-dsl

## About Calm DSL

Calm DSL describes a simpler Python3 based DSL for writing Calm blueprints. As Calm uses Services, Packages, Substrates, Deployments and Application Profiles as building blocks for a Blueprint, these entities can be defined as python classes. Their attributes can be specified as class attributes and actions on those entities (procedural runbooks) can be defined neatly as class methods. Calm blueprint DSL can also accept appropriate native data formats such as YAML and JSON, allowing the reuse and leveraging that work into the larger application lifecycle context of a Calm blueprint.

### Why Python3 as DSL ?

Language design is black art, and building upon a well-established language is design-wise a big win. The language has also solved many issues like scoping, modules, if-else, inheritance, etc. Well established languages have great tooling support: IDEs, syntax checkers, third-party modules, coding practices, better readability, editing, syntax highlighting, code completion, versioning, collaboration, etc. They see much more community improvements as well. Python specifically comes with a very good REPL (read–eval–print-loop). Having an interactive prompt to play around and slowly build objects is an order-of-magnitude improvement in developer productivity. Python is very easy language to learn and use; and most of the ITOps/DevOps community already use Python for scripting.

## Getting Started
 - Setup: `calm init dsl`. Please fill in the right Prism Central (PC) settings.
 - Server status: `calm get server status`. Check if Calm is enabled on PC & Calm version is >=2.9.7.
 - Config: `calm show config`. Check if you have the right config. By default, config is stored at `~/.calm/config.ini`. Please see `calm set config --help` for details to update config.
 - First blueprint: `calm init bp`. This will create a folder `HelloBlueprint` with all the necessary files. `HelloBlueprint/blueprint.py` is the main blueprint DSL file. Please read the comments in the beginning of the file for more details about the blueprint.
 - Compile blueprint: `calm compile bp --file HelloBlueprint/blueprint.py`. This command will print the compiled blueprint JSON.
 - Create blueprint on Calm Server: `calm create bp --file HelloBlueprint/blueprint.py --name <blueprint_name>`. Please use a unique name for `<blueprint_name>`.
 - List blueprints: `calm get bps`. You can also pass in filters like `calm get bps --name <blueprint_name>` and so on. Please look at `calm get bps --help`.
 - Describe blueprint: `calm describe bp <blueprint_name>`. It will print a summary of the blueprint.
 - Launch blueprint to create Application: `calm launch bp <blueprint_name> --app_name <app_name> -i`
 - List apps: `calm get apps`.
 - Describe app: `calm describe app <app_name>`. It will print a summary of the application and the current application state. Use `calm describe app <name> 2>/dev/null --out json | jq '.["status"]'` to get fields from the app json. More info on how to use `jq` [here](https://stedolan.github.io/jq/tutorial/).
 - Delete app: `calm delete app <app_name>`. You can delete multiple apps using: `calm get apps -q | xargs -I {} calm delete app {}`.

## [Runbooks](docs/01-Calm-Terminology#runbooks)
 - First runbook: `calm init runbook`. This will create a folder `HelloRunbook` with all the necessary files. `HelloRunbook/runbook.py` is the main runbook DSL file. Please read the comments in the beginning of the file for more details about the runbook.
 - Compile runbook: `calm compile runbook --file HelloRunbook/runbook.py`. This command will print the compiled runbook JSON.
 - Create runbook on Calm Server: `calm create runbook --file HelloRunbook/runbook.py --name <runbook_name>`. Please use a unique name for `<runbook_name>`.
 - List runbooks: `calm get runbooks`. You can also pass in filters like `calm get runbooks --name <runbook_name>` and so on. Please look at `calm get runbooks --help`.
 - Describe runbook: `calm describe runbook <runbook_name>`. It will print a summary of the runbook.
 - Execute runbook: `calm run runbook <runbook_name>`. Please look at `calm run runbook -h` for more info.
 - List runbook executions: `calm get runbook_executions`.
 - Watch runbook execution: `calm watch runbook_execution <runlog_id>`. It will display the runbook execution.
 - Pause runbook execution: `calm pause runbook_execution <runlog_id>`. It will pause the running runbook execution.
 - Resume runbook execution: `calm resume runbook_execution <runlog_id>`. It will play/resume the paused runbook execution.
 - Abort runbook execution: `calm abort runbook_execution <runlog_id>`. It will abort the runbook execution.

## Docker
 - Latest image: `docker pull ntnx/calm-dsl`
 - Run: `docker run -it ntnx/calm-dsl`

## Dev Setup

MacOS:
 - Install [Xcode](https://apps.apple.com/us/app/xcode/id497799835)
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

 - [Calm Terminology](docs/01-Calm-Terminology/)
 - [DSL Blueprint Architecture](docs/02-DSL-Blueprint-Architecture/)
 - [DSL Lab](docs/03-Quickstart/)

## Video Links
 - [Workstation Setup](https://youtu.be/uIZmHQhioZg)
 - [Blueprint & App management](https://youtu.be/jb-ZllhaROs)
 - [Calm DSL Blueprint Architecture](https://youtu.be/Y-6eq91rtSw)

## [Blogs](https://www.nutanix.dev/calm-dsl/)
 - [Introducing the Nutanix Calm DSL](https://www.nutanix.dev/2020/03/17/introducing-the-nutanix-calm-dsl/)
 - [Creating Custom Blueprint](https://www.nutanix.dev/2020/03/30/nutanix-calm-dsl-creating-custom-blueprint/)
 - [Generating VM Specs](https://www.nutanix.dev/2020/04/06/nutanix-calm-dsl-generating-vm-specs/)
 - [Run Custom Actions](https://www.nutanix.dev/2020/04/17/nutanix-calm-dsl-run-custom-actions/)
 - [Remote Container Development (Part 1)](https://www.nutanix.dev/2020/04/24/nutanix-calm-dsl-remote-container-development-part-1/)

## Demos
 - [Zero-touch CI/CD - VDI Template Creation with Nutanix Calm DSL](https://youtu.be/5k_K7idGxsI)
