# calm-dsl-engine

## WHY

The current Calm Blueprint JSON is not human readable (leave alone writable).
To build a new (human friendly) Blueprint DSL, the conventional approach is to use YAML (or JSON). We disagree, and think using a nice programming language is a much more scalable design. We think it should be python.

For three big reasons:
 - Language design is black art, and building upon a well-established language is design-wise a big win. The language has also solved many issues like scoping, modules, if-else, inheritance, etc
 - Well established languages have great tooling support: IDEs, syntax checkers, third-party modules, coding practices. They see much more community improvements as well (compare the performance of Python 3.0 vs 3.6 vs PyPy)
 - REPL: Python specifically comes with a very good REPL (read–eval–print loop). Having an interactive prompt to play around and slowly build objects is an order-of-magnitude improvement in developer productivity. Python inbuilt REPL (and also Jupyter (https://jupyter.org) which we will package) is very nice.

For more YAML bashing, see this [tweet](https://twitter.com/laserllama/status/1063777131736571905) from the creator of Ansible. Also, look at the [#noyaml](https://twitter.com/hashtag/noyaml?src=hash) movement which is now evident due to adoption of Kubernetes.

## WHAT

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

## ToDo

 - Prototype ([Demoscript](https://docs.google.com/document/d/1Psr8wPD73xCV6r3ILMEIx4Zf-nlN8H2kzMfGWO2A8_Q/edit))
   - Upload bp json for single VM to calm server
     - Add bp metadata (projects, etc)
     - ~Use same key names as v3 apis (use `x-calm-dsl-key` later to map to v3 schema)~
     - ~Add `RefType`~
     - ~Add connection handle to talk to server [Kiran]~
     - ~Add VariableType to entities~
   - ~Validate bp~
   - Launch bp
 - Language Enhancements:
   - Add Port type - tcp/udp
   - List of supported protocols - ssh
   - EnumType support
   - SecretType for credentials (file/vault)
 - Elegance wishlist
   - ~Allow inline definition of stateless classes like `Port`~
   - Show required vs optional attributes
   - ~Add YAML dumper~
   - ~Make all attrs available on the class for ease of discovery and use~
 - DSLs
   - DSL for runbooks
   - DSL for policies (quotas and notification)
   - DSL for apps (for app LCM)
 - Mega ToDo:
   - Generate idiomatic python code from blueprint JSON (decompile)
 - Build CLI tooling to interact with calm-server [Sen]
 - ~Build docker container for jupyter + DSL~
 - ~Make License as GPL~
 - ~Get rid of attributes field~
