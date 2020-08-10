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

## Project
- Create user: `calm create user --name <principal_name> --directory <directory_service>`.
- Create user-group: `calm create group -- name <distinguished_name_of_group>`/
- List users/user-groups: `calm get users/groups`.
- Delete user/user-group: `calm delete user/group <name>`. It will print summary of user/group.
- List directory services: `calm get directory_services`
- Compile project: `calm compile project --file <project_file_location>`.
- Create project: `calm create project --file <project_file_location>`.
- List projects: `calm get projects`
- Describe project: `calm describe project <project_name>`. It will print summary of project.
- Update project using dsl file: `calm update project <project_name> --file <project_file_location>`.
- Update project using cli switches: `calm update project --add_user/--remove_user <user_name> --add_group/--remove_group <group_name>`.
- Delete project: `calm delete project <project_name>`.
- Create ACP: `calm create acp --role <role_name> --project <project_name> --name <acp_name>`. Custom roles are not supported for acp creation.
- List ACPs: `calm get acps --project <project_name>`.
- Read ACP: `calm describe acp <acp_name> --project <project_name>`.
- Update ACP: `calm update acp <acp_name> --project <project_name> --add_user/--remove_user <user_name> --add_group/--remove_group <group_name>`
- Delete ACP: `calm delete acp <acp_name> --project <project_name>`.
- Note: Project option is required for acp commands.

## Blueprint
 - First blueprint: `calm init bp`. This will create a folder `HelloBlueprint` with all the necessary files. `HelloBlueprint/blueprint.py` is the main blueprint DSL file. Please read the comments in the beginning of the file for more details about the blueprint.
 - Compile blueprint: `calm compile bp --file HelloBlueprint/blueprint.py`. This command will print the compiled blueprint JSON.
 - Create blueprint on Calm Server: `calm create bp --file HelloBlueprint/blueprint.py --name <blueprint_name>`. Please use a unique name for `<blueprint_name>`.
 - List blueprints: `calm get bps`. You can also pass in filters like `calm get bps --name <blueprint_name>` and so on. Please look at `calm get bps --help`.
 - Describe blueprint: `calm describe bp <blueprint_name>`. It will print a summary of the blueprint.
 - Launch blueprint to create Application: `calm launch bp <blueprint_name> --app_name <app_name> -i`

## Application
 - List apps: `calm get apps`. Use `calm get apps -q` to show only application names.
 - Describe app: `calm describe app <app_name>`. It will print a summary of the application and the current application state. Use `calm describe app <name> 2>/dev/null --out json | jq '.["status"]'` to get fields from the app json. More info on how to use `jq` [here](https://stedolan.github.io/jq/tutorial/).
 - Delete app: `calm delete app <app_name>`. You can delete multiple apps using: `calm get apps -q | xargs -I {} calm delete app {}`.
 - Run action on application: `calm run action <action_name> --app <application_name>`
 - Start an application: `calm start app <app_name>`
 - Stop an application: `calm stop app <app_name>`
 - Restart an application: `calm restart app <app_name>`
 - Display app action runlogs: `calm watch app <app_name>`
 - Watch app action runlog: `calm watch action_runlog <runlog_uuid> --app <application_name>`
 - Download app action runlogs: `calm download action_runlog <runlog_uuid> --app <application_name> --file <file_name>`

## Decompile
Decompilation is process to consume json data for any entity and convert it back to dsl python helpers/classes. Currently decompile is supported for converting blueprint json to python files. Summary of support for blueprint decompilation(Experimental feature):
- Python helpers/classes are automatically generated with the use of jinja templates.
- Generated python file is formatted using [black](https://github.com/psf/black)
- Default values for most of the entities will be shown in decompiled file.
- Separate files are created under `.local` directory in decompiled blueprint directory for handling secrets used inside blueprints i.e. passwords etc.
- Separate files are created under `scripts` directory in decompiled blueprint directory for storing scripts used in variable, tasks, guest customization etc.
- Provider specs (Other than AHV) / Runtime editables for substrates  are stored in `specs` directory in blueprint directory.
- Name of created files are taken from the context of variable/task. For ex: Filename for service action task script: Service_MySQLService_Action___create___Task_Task1
- Decompile existing server blueprint: `calm decompile bp <bp_name>`. Use `calm decompile bp <bp_name> --with_secrets` to fill the value for secrets used inside blueprint interactively while decompiling blueprint.
- Decompile bp from existing json file: `calm decompile bp --file <json_file_location>`.
- Decompile marketplace blueprint: `calm decompile marketplace_bp <bp_name> --version <bp_version>`.
- Note: Decompliation support for providers other than AHV are best effort(Experimental).

## Docker
 - Latest image: `docker pull ntnx/calm-dsl`
 - Run: `docker run -it ntnx/calm-dsl`

## Dev Setup

MacOS:
 - Install [Xcode](https://apps.apple.com/us/app/xcode/id497799835)
 - Install homebrew: `/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`.
 - Install python3, git and openssl: `brew install git python3 openssl`.
 - Install virtualenv: `pip install virtualenv`
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
 - [From UI to Code – Calm DSL and Blueprint Decompile](https://www.nutanix.dev/2020/07/20/from-ui-to-code-calm-dsl-and-blueprint-decompile/)

## Demos
 - [Zero-touch CI/CD - VDI Template Creation with Nutanix Calm DSL](https://youtu.be/5k_K7idGxsI)
 - [Integrating with Azure DevOps CI/CD pipeline](https://youtu.be/496bvlIi4pk)
