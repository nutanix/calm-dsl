
# Snapshot Restore
Adding a snapshot (or restore) config in a profile will auto-generate a profile-level snapshot (or restore) action - Snapshot_<config_name> (or Restore_<config_name>) - which can be run using `calm run action`.
- As of now we suport for snapshot-restore for `nutanix` provider.
- Sample [Blueprint](../../examples/AHV_CONFIG/snapshot_restore/demo_blueprint.py)  containg snapshot-restore configuration.

## CLI commands
- `calm get protection-policies -p <project>`: Lists protection policies corresponding to the project (create/update/delete using DSL not supported in this release)

## Built-in Models

### AppProtection.ProtectionPolicy
#### Input  Parameters
- <ins>name</ins>
- rule_name - name of the protection rule (from `calm get protection-policies`)

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

## Running Snapshot and Restore Actions
Snapshot and Restore Actions can be run like any other profile-level action using `calm run action`.
```
calm run action Snapshot_<config_name> -a <app_name>
calm run action Restore_<config_name> -a <app_name>
```
Snapshot name is supplied as a runtime argument while running the snapshot action, and similarly, recovery group can be chosen while running the restore action.

# App edit
Adding a update config in a profile will auto-generate a profile-level patch action - <config_name> - which can be run using `calm update app <app-name> <config-name>`. 
- As of now we suport for app edit for `nutanix` provider.
- Sample [Blueprint](../../examples/multivm_app_edit/blueprint.py) containing app-edit configuration

## Built-in Models
### AhvUpdateConfigAttrs
#### Input Parameters
- memory (optional) - PatchField.Ahv.memory
- vcpu (optional) - PatchField.Ahv.vcpu
- numsocket (optional) - PatchField.Ahv.numsocket
- disk_delete (optional) - Boolean to make disk delete runtime
- categories_delete (optional) - Boolean to make category delete runtime
- nic_delete (optional) - Boolean to make nic delete runtime
- categories_add (optional) - Boolean to make category add runtime
- nics (optional) - list of nics of type PatchField.Ahv.Nics
- disks (optional) - list of disks of type PatchField.Ahv.Disks
- caegories (optional) - list of category of type PatchField.Ahv.Category

#### Example
```
class AhvUpdateAttrs(AhvUpdateConfigAttrs):
    memory = PatchField.Ahv.memory(value="2", operation="equal", max_val=0, min_val=0, editable=False)
    vcpu = PatchField.Ahv.vcpu(value="2", operation="equal", max_val=0, min_val=0)
    numsocket = PatchField.Ahv.numsocket(value="2", operation="equal", max_val=0, min_val=0)
    disk_delete = True
    categories_delete = True
    nic_delete = True
    categories_add = True
    nics = [
        PatchField.Ahv.Nics.delete(index=1, editable=True),
        PatchField.Ahv.Nics.add(
            AhvVmNic.DirectNic.ingress(
                subnet="nested_vms", cluster="auto_cluster_prod_1a5e1b6769ad"
            ),
            editable=False,
        ),
    ]
    disks = [
        PatchField.Ahv.Disks.delete(index=1, editable=True),
        PatchField.Ahv.Disks.modify(
            index=2, editable=True, value="2", operation="equal", max_val=4, min_val=1
        ),
        PatchField.Ahv.Disks.add(
            AhvVmDisk.Disk.Pci.allocateOnStorageContainer(10),
            editable=False,
        ),
    ]
    categories = [
        PatchField.Ahv.Category.add({"TemplateType": "Vm"}),
        PatchField.Ahv.Category.delete({"AppFamily": "Demo", "AppType": "Default"}),
    ]
```

### PatchField.Ahv.memory
#### Input Parameters
- value - updated value
- operation - operation (equal/increase/decrease)
- max_value (optional) - max value if editable
- min_value (optional) - min value if ediatble
- editable (optional) - editable boolean
### PatchField.Ahv.vcpu
#### Input Parameters
- value - updated value
- operation - operation (equal/increase/decrease)
- max_value (optional) - max value if editable
- min_value (optional) - min value if ediatble
- editable (optional) - editable boolean
### PatchField.Ahv.numsocket
#### Input Parameters
- value - updated value
- operation - operation (equal/increase/decrease)
- max_value (optional) - max value if editable
- min_value (optional) - min value if ediatble
- editable (optional) - editable boolean
### PatchField.Ahv.Nics.add
#### Input Parameters
- Ahv nic object
- editable (optional) - editable boolean
### PatchField.Ahv.Nics.delete
- index - index of nic to be deleted
### PatchField.Ahv.Disks.add
- Ahv disk object
- editable (optional) - editable boolean
### PatchField.Ahv.Disks.modify
- index - index of disk to be modified
- value - updated value
- operation - operation (equal/increase/decrease)
- max_value (optional) - max value if editable
- min_value (optional) - min value if ediatble
- editable (optional) - editable boolean
### PatchField.Ahv.Disks.delete
- index - index of disk to be deleted
### PatchField.Ahv.Category.add
- dict of category
### PatchField.Ahv.Category.delete
- dict of category

### Profile
- Added `patch_list` attributes.
```
from calm.dsl.builtins import AhvUpdateConfigAttrs
class HelloProfile(Profile):

    deployments = [HelloDeployment]
    patch_list = [AppEdit.UpdateConfig("Sample update", target=ref(HelloDeployment), patch_attrs=AhvUpdateAttrs)]
```

### Triggering Patch defined on a running APP
```
calm update app example_app example_update_config
```


# *Brownfield Application
From Calm v3.3.0, user can launch Greenfield blueprint to create Brownfield application by supplying brownfield deployments that will override the existing deployment configuration.
- As of now we suport for app edit for nutanix provider.
- Sample [file](../../examples/Brownfield/separate_file_example/brownfield_deployments.py) containing brownfield-deployment configuration.
- Note: Name of deployment which user wants to override should exists in blueprint.

## CLI commands

- `calm get brownfield vms -p <project> -a <account_name>`: Added account cli option, that user should provide if there are multiple accounts in the given project.

- `calm launch bp <bp_name> -b <brownfield_deployments_file_location> -n <app_name>`. Command will launch existing blueprint using brownfield deployments to create brownfield application. 


# *Vm Recovery Points

 From Calm v3.3.0, user can create and launch a blueprint having vm-recovery-point instead of vm-configuration for ahv substrates. 
- Sample [Blueprint](../../tests/vm_recovery_point/blueprint.py) containing vm-recovery-point configuration.
- Note: Only CrashConsistent vm_recovery_point are allowed.

 ## CLI commands

 - `calm get vm-recovery-points -p <project_name> -a <account_name>`: Command will list the vm recovery points for given account in a project.

## Builtin-Models

- Added `AhvVmRecoveryResources` model which specify the vm resources to be overrided after recovery of vm.

```
class MyAhvVmResources(AhvVmRecoveryResources):
    """
        [NumVcpusPerSocket, NumSockets, MemorySizeMb, NicList, GPUList, vm_name] can be overrided
    """

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    nics = [AhvVmNic(NETWORK1)]
```

- Added `Ref.RecoveryPoint(name, uuid)` which consumes name/uuid of recovery point and returns ref object for recovery point.

```
Ref.RecoveryPoint(name=VM_RECOVERY_POINT_NAME)
```

- Added `ahv_vm_recovery_spec` helper which consumes vm-recovery-point details and returns the ahv-vm-recovery-spec object.

```
ahv_vm_recovery_spec(
    recovery_point=Ref.RecoveryPoint(name=VM_RECOVERY_POINT_NAME),
    vm_name="AhvRestoredVm",
    vm_override_resources=MyAhvVmResources,
)
```

- Added `vm_recovery_spec` attribute which specify the vm_recovery_spec used for the given substrare.

```
class AhvVmSubstrate(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_type = "AHV_VM"
    vm_recovery_spec = ahv_vm_recovery_spec(
        recovery_point=Ref.RecoveryPoint(name=VM_RECOVERY_POINT_NAME),
        vm_name="AhvRestoredVm",
        vm_override_resources=MyAhvVmResources,
    )
```

*: *Features are Calm-DSL specific. No support for UX/UI is available in Calm v3.3.0*.
