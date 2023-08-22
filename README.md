[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

![Build](https://github.com/nutanix/calm-dsl/workflows/Setup%20&%20build%20calm-dsl/badge.svg)

# calm-dsl

## About Calm DSL

Calm DSL describes a simpler Python3 based DSL for writing Calm blueprints. As Calm uses Services, Packages, Substrates, Deployments and Application Profiles as building blocks for a Blueprint, these entities can be defined as python classes. Their attributes can be specified as class attributes and actions on those entities (procedural runbooks) can be defined neatly as class methods. Calm blueprint DSL can also accept appropriate native data formats such as YAML and JSON, allowing the reuse and leveraging that work into the larger application lifecycle context of a Calm blueprint.

### Why Python3 as DSL ?

Language design is black art, and building upon a well-established language is design-wise a big win. The language has also solved many issues like scoping, modules, if-else, inheritance, etc. Well established languages have great tooling support: IDEs, syntax checkers, third-party modules, coding practices, better readability, editing, syntax highlighting, code completion, versioning, collaboration, etc. They see much more community improvements as well. Python specifically comes with a very good REPL (read–eval–print-loop). Having an interactive prompt to play around and slowly build objects is an order-of-magnitude improvement in developer productivity. Python is very easy language to learn and use; and most of the ITOps/DevOps community already use Python for scripting.

## Getting Started for Developers

### Initialization
 - Setup: `calm init dsl`. Please fill in the right Prism Central (PC) settings.
 - Server status: `calm get server status`. Check if Calm is enabled on PC & Calm version is >=2.9.7.
 - Config: `calm show config`. Please see `calm set config --help` to update configuration.

### Calm DSL Context
Context info includes server, project and log configuration for dsl operations.
- Flow: Context info is taken from config file passed inline with cli command or environment data or default config file stored mentioned in `~/.calm/init.ini`.
- Environment variables for server configuration: `CALM_DSL_PC_IP`, `CALM_DSL_PC_PORT`, `CALM_DSL_PC_USERNAME`, `CALM_DSL_PC_PASSWORD`.
- Environment variable for project configuration: `CALM_DSL_DEFAULT_PROJECT`.
- Environment variable for log configuration: `CALM_DSL_LOG_LEVEL`.
- Environment variables for init configuration: `CALM_DSL_CONFIG_FILE_LOCATION`, `CALM_DSL_LOCAL_DIR_LOCATION`, `CALM_DSL_DB_LOCATION`.
- Config file parameter: `calm --config/-c <config_file_location> ...`
- Show config in context: `calm show config`.

### Blueprint
 - First blueprint: `calm init bp`. This will create a folder `HelloBlueprint` with all the necessary files. `HelloBlueprint/blueprint.py` is the main blueprint DSL file. Please read the comments in the beginning of the file for more details about the blueprint.
 - Compile blueprint: `calm compile bp --file HelloBlueprint/blueprint.py`. This command will print the compiled blueprint JSON.
 - Create blueprint on Calm Server: `calm create bp --file HelloBlueprint/blueprint.py --name <blueprint_name>`. Please use a unique name for `<blueprint_name>`.
 - List blueprints: `calm get bps`. You can also pass in filters like `calm get bps --name <blueprint_name>` and so on. Please look at `calm get bps --help`.
 - Describe blueprint: `calm describe bp <blueprint_name>`. It will print a summary of the blueprint.
 - Launch blueprint to create Application: `calm launch bp <blueprint_name> --app_name <app_name> -i`
 - Launch blueprint using environment configuration: `calm launch bp <blueprint_name> --app_name <app_name> --environment <env_name>`
 - Publish blueprint to marketplace manager: `calm publish bp <bp_name> --version <version> --project <project_name>`. Please look at `calm publish bp --help`.

### Application
 - List apps: `calm get apps`. Use `calm get apps -q` to show only application names.
 - Create app: `calm create app -f <file>`. Command will create blueprint and launch it to get application. Please look at `calm create app -h`.
 - Describe app: `calm describe app <app_name>`. It will print a summary of the application and the current application state. Use `calm describe app <name> 2>/dev/null --out json | jq '.["status"]'` to get fields from the app json. More info on how to use `jq` [here](https://stedolan.github.io/jq/tutorial/).
 - Delete app: `calm delete app <app_name>`. You can delete multiple apps using: `calm get apps -q | xargs -I {} calm delete app {}`.
 - Run action on application: `calm run action <action_name> --app <application_name>`
 - Start an application: `calm start app <app_name>`
 - Stop an application: `calm stop app <app_name>`
 - Restart an application: `calm restart app <app_name>`
 - Display app action runlogs: `calm watch app <app_name>`
 - Watch app action runlog: `calm watch action_runlog <runlog_uuid> --app <application_name>`
 - Download app action runlogs: `calm download action_runlog <runlog_uuid> --app <application_name> --file <file_name>`

### Brownfield Application
- Two ways to declare brownfield deployments in dsl: User can define brownfield deployments in blueprint [file](examples/Brownfield/inline_example/blueprint.py) OR he can declare brownfield deployments in separate [file](examples/Brownfield/separate_file_example/brownfield_deployments.py) and pass it as cli parameter while creating brownfield application.
- List Brownfield vms: `calm get brownfield vms --project <project_name> --type [AHV_VM|AWS_VM|AZURE_VM|GCP_VM|VMWARE_VM]`. Please use `--account` cli option, if project has multiple accounts for a provider type.
- Compile Blueprint: `calm compile bp -f <blueprint_file_location> -b <brownfield_deployments_file_location>`.
- Create Brownfield Application: `calm create app -f <bluprint_file_location> -b <brownfield_deployments_file_location> -n <app_name> -i`.
- Create Brownfield Application using existing blueprint: `calm launch bp <bp_name> -b <brownfield_deployments_file_location> -n <app_name>`. Command will launch existing blueprint to create brownfield application (3.3.0 onwards). Look at sample file [here](examples/Brownfield/separate_file_example/brownfield_deployments.py).

### Decompiling Blueprints (`.json`->`.py`)
Decompilation is process to consume json data for any entity and convert it back to dsl python helpers/classes. Currently, decompile is supported for converting blueprint json to python files. Summary of support for blueprint decompilation(Experimental feature):
- Python helpers/classes are automatically generated with the use of jinja templates.
- Generated python file is formatted using [black](https://github.com/psf/black)
- Default values for most of the entities will be shown in decompiled file.
- Separate files are created under `.local` directory in decompiled blueprint directory for handling secrets used inside blueprints i.e. passwords etc.
- Separate files are created under `scripts` directory in decompiled blueprint directory for storing scripts used in variable, tasks, guest customization etc.
- Provider specs (Other than AHV) / Runtime editables for substrates  are stored in `specs` directory in blueprint directory.
- Name of created files are taken from the context of variable/task. For ex: Filename for service action task script: Service_MySQLService_Action___create___Task_Task1
- Decompile blueprint with secrets: Decompile the blueprint using the  `--passphrase` or`-ps` flag. This will create files for all secret files and have encrypted secrets in them. This also creates a `decompiled_secrets.bin` file (Not to be changed) which is used during blueprint create for validating if the encrypted secret value is not modified while launching the blueprint again.
- [Deprecated] Decompile blueprint : `calm decompile bp <bp_name>`. Use `calm decompile bp <bp_name> --with_secrets` to fill the value for secrets at runtime in the terminal which are used inside blueprint.
- Decompile bp from existing json file: `calm decompile bp --file <json_file_location>`.
- Decompile marketplace blueprint: `calm decompile marketplace bp <bp_name> --version <bp_version>`.
- Decompile bp to a location: `calm decompile bp <bp_name> --dir <bp_dir>`. It will decompile blueprint entities to `bp_dir` location.
- Note: Decompliation support for providers other than AHV is experimental.

### Runbooks
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
 - Please look [here](docs/01-Calm-Terminology#runbooks) for more details.

### Decompiling Runbooks (`.json`->`.py`)
Decompilation is process to consume json data for any entity and convert it back to dsl python helpers/classes. Currently, decompile is supported for converting blueprint and runbook jsons to python files. Summary of support for runbook decompilation(Experimental feature):
- Python helpers/classes are automatically generated with the use of jinja templates.
- Generated python file is formatted using [black](https://github.com/psf/black)
- Default values for most of the entities will be shown in decompiled file.
- Separate files are created under `.local` directory in decompiled runbook directory for handling secrets used inside runbooks i.e. passwords etc.
- Separate files are created under `scripts` directory in decompiled runbook directory for storing scripts used in variable, tasks etc.
- Name of created files are taken from the context of variable/task. For ex: Filename for task script: _Runbook_test_rb_1_Task_Task2.py
- Decompile existing server runbook: `calm decompile runbook <runbook_name>`.
- Decompile runbook from existing json file: `calm decompile runbook --file <json_file_location>`.
- Decompile runbook to a location: `calm decompile runbook <runbook_name> --dir <runbook_dir>`. It will decompile runbook entities to `runbook_dir` location.

### Task Library
 - List task library items: `calm get library tasks`. Use `calm get library tasks -q` to show only task library names.
 - Create task library item: `calm create library task -f <file>`. Command will create task under library. Please look at `calm create library task -h`.
 - Describe task library item: `calm describe library task <task_name>`. It will print a summary of the task and the current state. Use `calm describe library task <name> 2>/dev/null --out json | jq '.["status"]'` to get fields from the task json. More info on how to use `jq` [here](https://stedolan.github.io/jq/tutorial/).
 - Delete task library item: `calm delete library task <task_name>`. You can delete multiple task library items using: `calm get library tasks -q | xargs -I {} calm delete library task {}`.
 - Import script files as task library item: `calm import library task -f <files_name>(.json, .sh, .escript, .ps1)`. Create task under library by passing scripts shell, powershell etc.


## Getting started for Admins

### Initialization
 - Setup: `calm init dsl`. Please fill in the right Prism Central (PC) settings.
 - Server status: `calm get server status`. Check if Calm is enabled on PC & Calm version is >=2.9.7.
 - Config: `calm show config`. Please see `calm set config --help` to update configuration.

### Calm DSL Context
Context information includes server, project and log configuration for dsl operations.
- Flow: Context info is taken from config file passed inline with cli command or environment data or default config file stored mentioned in `~/.calm/init.ini`.
- Environment variables for server configuration: `CALM_DSL_PC_IP`, `CALM_DSL_PC_PORT`, `CALM_DSL_PC_USERNAME`, `CALM_DSL_PC_PASSWORD`.
- Environment variable for project configuration: `CALM_DSL_DEFAULT_PROJECT`.
- Environment variable for log configuration: `CALM_DSL_LOG_LEVEL`.
- Environment variables for init configuration: `CALM_DSL_CONFIG_FILE_LOCATION`, `CALM_DSL_LOCAL_DIR_LOCATION`, `CALM_DSL_DB_LOCATION`.
- Config file parameter: `calm --config/-c <config_file_location> ...`
- Show config in context: `calm show config`.

### Roles
Use `calm get roles` to list all roles in PC. The below roles are relevant for Calm:
 - `Prism Admin`: Day-to-day admin of a Nutanix deployment. Manages the infrastructure and platform, but cannot entitle other users to be admins.
 - `Project Admin`: Team lead to whom cloud administration gets delegated in the context of a project. Manages end users within the project and has full access to their entities.
 - `Developer`: Application developer within a team. Authors blueprints, tests deployments, and publishes applications for other project members.
 - `Operator`: Owner of team applications at runtime. Works on existing application deployments, exercises blueprint actions.
 - `Consumer`: Lifecycle manager for team applications. Launches blueprints and controls their lifecycle and actions.

### Directory Services
- Current directory services are listed under `calm get directory_services`.

### Users
- Create user: `calm create user --name <principal_name> --directory <directory_service>`.
- List users: `calm get users`. Get users, optionally filtered by a string
- Delete user: `calm delete user <principal_name>`

### User-Groups
- Create group: `calm create group <distinguished_name>`.
- List groups: `calm get groups`. Get user groups, optionally filtered by a string
- Delete group: `calm delete group <distinguished_name>`

### Projects
- Compile project: `calm compile project --file <project_file_location>`. This command will print the compiled project JSON. Look at sample file [here](examples/Project/demo_project.py) and [here](examples/Project/project_with_env.py).
- Create project on Calm Server: `calm create project --file <project_file_location> --name <project_name> --description <description>`. Use `no-cache-update` flag to skip cache updations post operation.
- List projects: `calm get projects`. Get projects, optionally filtered by a string
- Describe project: `calm describe project <project_name>`. It will print summary of project.
- Update project using dsl file: `calm update project <project_name> --file <project_file_location>`. Environments will not be updated as part of this operation. Use `no-cache-update` flag to skip cache updations post operation.
- Update project using cli switches: `calm update project <project_name> --add_user/--remove_user <user_name> --add_group/--remove_group <group_name> --add_account/--remove_account <account_name>`.
- Delete project: `calm delete project <project_name>`. Use `no-cache-update` flag to skip cache updations post operation.
- Enable/Disable Quotas: 
 - During project creation, it checks if quotas are avaialble in project payload (json or python file). If it is there, then quotas are enabled in the project.
 - During project updation, use the following flags `--enable-quotas/-eq` and `--disable-quotas/-dq`
  - If the project already has quotas set and enabled and quotas are present in {project_file} then the quotas would be updated
  - If the project already has quotas set and enabled and there are no quotas in {project_file} then the original quotas in the projects would be persisted.
  - If the project doesn't have quotas enabled/set and the {project_file} has quotas then the quotas would be enabled and set in the project.
- Note: While using `no-cache-update` flag in project create and update commands, user should not pass environment object in the project model. User should update the cache separately after creation/updation of projects. Feature is experimental and will be discontinued after [#184](https://github.com/nutanix/calm-dsl/issues/184) is fixed.

### Environments
- Compile environment: `calm compile environment --file <env_file_location> --project <project_name>`. Command will print the compiled environment JSON. Look at sample file [here](examples/Environment/sample_environment.py)
- Create environment to existing project: `calm create environment --file <env_file_location> --project <project_name> --name <environmet_name>`. Use `no-cache-update` flag to skip cache updations post operation.
- Update environment: `calm update environment <environment_name> --file <env_file_location> --project <project_name>`. Use `no-cache-update` flag to skip cache updations post operation.
- List environments: `calm get environments --project <project_name>`. Get environments of project.
- Delete environment: `calm delete environment <environment_name> --project <project_name>`. Use `no-cache-update` flag to skip cache updations post operation.

### Access Control Policies
Access control policies ensures that a project member can access only the entities or perform only the actions defined in the role assigned to that project member.
- Create ACP: `calm create acp --role <role_name> --project <project_name> --user <user_principal_name> --group <group_distinguished_name> --name <acp_name>`. It is used to assign given role to users/groups. Parameters `user` and `group` can be provided multiple times.
- List ACPs: `calm get acps --project <project_name>`.Get acps, optionally filtered by a string
- Describe ACP: `calm describe acp <acp_name> --project <project_name>`.
- Update ACP: `calm update acp <acp_name> --project <project_name> --add_user/--remove_user <user_name> --add_group/--remove_group <group_name>`. Paramters `add_user`, `remove_user`, `add_group` and `remove_group` can be provided multiple times.
- Delete ACP: `calm delete acp <acp_name> --project <project_name>`.

### Examples
Sample Project flow for `Admin` users:
- Project Creation: `calm create project --file "project_file_location" --name "project_name"`
- Create users: `calm create user --name "user_1" --directory "user_1_directory_service"`
- Create User-Group: `calm create group "group_1"`
- Update Project for adding created users/groups to project: `calm update project "project_name" --add_user "user_1" --add_user "user_2" --add_group "group_1" --add_group "group_2"`.
- Create ACP for `Project Admin` role assignment to project users/groups:  `calm create acp --role "Project Admin" --project "project_name" --user "user_1" --user "user_2" --group "group_1" --group "group_2" --name "acp_name"`

Sample Project Flow for `Project Admin` users:
- Update project for adding/removing users or groups in project: `calm update project "project_name" --add_user "user_3" --remove_user "user_2" --add_group "group_3" --remove_group "group_2"`.
- Create ACPs for other roles in project i.e. Consumer, Developer, Operator. Ex: `calm create acp --role "Developer" --project "project_name" --user "user_3" --group "group_3" --name "acp_developer_name"`
- Update ACPs: `calm update acp "acp_developer_name" --project "project_name" --add_user "user_1" --remove_user "user_3" --add_group "group_1" --remove_group "group_3"`.

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
