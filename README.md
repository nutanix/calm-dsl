# calm-dsl-engine

Calm DSL Engine describes a simpler Python 3 based DSL for writing Calm blueprints.

Use:
 - `make _init_py3_centos` to setup your CentOS 7 VM for development.
 - `make dev` to create/use python3 virtualenv in `$TOPDIR/venv` and setup dev environment. Activate it by calling `source venv/bin/activate`. Use `deactivate` to deactivate virtualenv.
 - `make test` to run the test cases.
 - `make dist` to generate a `calm.dsl` python distribution.
 - `make gui` to install jupyter notebook and extensions in your virtualenv.
 - `make docker` to build docker container. (Assumes docker client is setup on your machine)
 - `make clean` to reset.


## ToDo

 - Language Enhancements:
   - Add Port type - tcp/udp
   - List of supported protocols - ssh
   - EnumType support
   - SecretType for credentials (file/vault)
 - Elegance wishlist
   - ~Allow inline definition of stateless classes like `Port`~
   - Show required vs optional attributes
   - ~Add YAML dumper~
   - ~Make all attrs available on the class for ease of discovery aand use~
 - DSLs
   - DSL for runbooks
   - DSL for policies (quotas and notification)
   - DSL for apps (for app LCM)
 - Mega ToDo:
   - Generate idiomatic python code from blueprint JSON (decompile)
 - Build CLI tooling to interact with calm-server
 - ~Build docker container for jupyter + DSL~
 - ~Make License as GPL~
 - ~Get rid of attributes field~
