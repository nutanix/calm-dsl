# calm-dsl-engine

Calm DSL Engine describes a simpler Python 3 based DSL for writing Calm blueprints.

Use:
 - `make _init` to setup your CentOS 7 VM for development. This will create a python 3 virtualenv in `$TOPDIR/venv` . Activate it by sourcing `$TOPDIR/venv/bin/activate`
 - `make dist` to generate a `calm.dsl` python distribution
 - `make test` to run the test cases


## ToDo

 - Add Port type - tcp/udp
 - List of supported protocols - ssh
 - EnumType support
 - Add YAML dumper
 - Allow inline definition of stateless classes like `Port`
 - ~Make License as GPL~
 - ~Get rid of attributes field~
