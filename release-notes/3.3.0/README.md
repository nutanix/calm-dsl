# Brownfield Application

## CLI commands

- `calm get brownfield vms -p <project> -a <account_name>`: Added account cli option, that user should provide if there are multiple accounts in the given project.

- `calm launch bp <bp_name> -b <brownfield_deployments_file_location> -n <app_name>`. Command will launch existing blueprint using brownfield deployments to create brownfield application. Sample file look [here](examples/Brownfield/separate_file_example/brownfield_deployments.py).

# Snapshot Restore
Adding a snapshot (or restore) config in a profile will auto-generate a profile-level snapshot (or restore) action - Snapshot_<config_name> (or Restore_<config_name>) - which can be run using `calm run action`.

## CLI commands
- `calm get protection_policies -p <project>`: Lists protection policies corresponding to the project (create/update/delete using DSL not supported in this release)

## Built-in Models

### AppProtection.ProtectionPolicy
#### Input  Parameters
- <ins>name</ins>
- rule_name - name of the protection rule (from `calm get protection_policies`)

### AppProtection.SnapshotConfig
#### Input Parameters
- <ins>name</ins>
- policy (optional) - Protection Policy object
- rule (optional) - App Protection Rule name
- target (optional) - corresponding deployment reference (defaults to the first deployment in the profile)
- restore_config (optional) - Restore Config reference (defaults to the first restore config in the profile)
- num_of_replicas (optional) - <b>"ONE"</b> or "ALL"
- description (optional)

### AppProtection.RestoreConfig
#### Input  Parameters
- <ins>name</ins>
- target (optional) - corresponding deployment reference (defaults to the first deployment in the profile)
- delete_vm_post_restore (optional) - boolean (<b>True</b>)
- description (optional)

### Profile
Added `snapshot_configs` and `restore_configs` attributes.
```
from calm.dsl.builtins import AppProtection
class HelloProfile(Profile):

    deployments = [HelloDeployment]
    restore_configs = [AppProtection.RestoreConfig("Sample Config1")]
    snapshot_configs = [AppProtection.SnapshotConfig("Sample Config2", policy=AppProtection.ProtectionPolicy("policy1"), restore_config=ref(restore_configs[0]))]
```

[Sample Blueprint](examples/AHV_CONFIG/snapshot_restore/demo_blueprint.py).

## Running Snapshot and Restore Actions
Snapshot and Restore Actions can be run like any other profile-level action using `calm run action`.
```
calm run action Snapshot_<config_name> -a <app_name>
calm run action Restore_<config_name> -a <app_name>
```
Snapshot name is supplied as a runtime argument while running the snapshot action, and similarly, recovery group can be chosen while running the restore action.
