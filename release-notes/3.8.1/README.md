
# Major Feats

1. Added `calm run-script` command which will test scripts for any syntactical errors. Supported scripts are: escripts, shell scripts, powershell, python. For more details refer <b>Playground</b> section of <b>Getting-Started</b> in [DSL-Documentation](https://www.nutanix.dev/docs/self-service-dsl/)

2. Added `-ak/--api-key` flag in `calm init dsl`, `calm set config` command to support api key authentication for SAAS Instance. For more details refer <b>Saas Instance Login</b> section of <b>DSL-Configuration -> Initialization</b> in [DSL-Documentation](https://www.nutanix.dev/docs/self-service-dsl/)

# Bug Fixes/Improvements

- Fixes `calm get marketplace bps` command failure in Calm-VM 3.8.0 for objects MPI.
- Fixes `calm update app-migratable-bp` command failure for multi-profile multi-VM blueprint.
- Fixes failure while providing guest customization for AHV using command `calm create provider spec --type AHV_VM`
- Adds support to provide xml file path for guest customization while creating provider spec for AHV using `calm create provider spec --type AHV_VM`
- Endpoints of VM type will only be created if referenced VM is in current context project i.e VM is authorized for a given project. Similarly, only authorized VM can be used as target endpoint in runbook/blueprint.