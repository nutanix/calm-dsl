## Snapshot Restore Configs
### Model Description
#### Snapshot Config
`AppProtection.SnapshotConfig.[SnapshotType]`

- SnapshotType (optional) - <b>CrashConsistent</b>
##### Input  Parameters
- <ins>name</ins>
- policy (optional) - Ref object corresponding to the App Protection Policy to be used
- rule (optional) - App Protection Rule name
- target (optional) - corresponding deployment reference (defaults to the first deployment in the profile)
- restore_config (optional) - Restore Config reference (defaults to the first restore config in the profile)
- num_of_replicas (optional) - <b>"ONE"</b> or "ALL"
- description (optional)

#### Restore Config
`AppProtection.RestoreConfig`

##### Input  Parameters
- <ins>name</ins>
- target (optional) - corresponding deployment reference (defaults to the first deployment in the profile)
- delete_vm_post_restore (optional) - boolean (<b>True</b>)
- description (optional)

#### Protection Policy
`AppProtection.ProtectionPolicy`

##### Input  Parameters
- <ins>name</ins>
- rule_name - name of the protection rule (from `calm get protection-policies`)

### Usage

- #### Instantiate Configs under Profile
```python
from calm.dsl.builtins import AppProtection
class HelloProfile(Profile):

    deployments = [HelloDeployment]
    restore_configs = [AppProtection.RestoreConfig("Sample Config1")]
    snapshot_configs = [AppProtection.SnapshotConfig("Sample Config2", policy=AppProtection.ProtectionPolicy("policy1"), restore_config=ref(restore_configs[0]))]
```
