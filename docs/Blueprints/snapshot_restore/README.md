For AHV snapshot restore refer [here](../../../release-notes/3.3.0/README.md)

For VMware snapshot restore refer below:

1. `AppProtection.SnapshotConfig`: Contains classes `AppProtection.SnapshotConfig.Ahv` and `AppProtection.SnapshotConfig.Vmware` for nutanix and vmware provider respectively. `AppProtection.SnapshotConfig` defaults to Ahv class for backware compatibility.

2. `AppProtection.RestoreConfig`: Contains classes `AppProtection.RestoreConfig.Ahv` and `AppProtection.RestoreConfig.Vmware` for nutanix and vmware provider respectively. `AppProtection.RestoreConfig` defaults to Ahv class for backware compatibility.

Sample Profile class containing snapshot/restore configs for VMWARE provider.
```python
from calm.dsl.builtins import AppProtection
class VmwareProfile(Profile):

    deployments = [VmwDeployment]
    restore_configs = [
        AppProtection.RestoreConfig.Vmware(name="r1",
        target=ref(VmwDeployment))
    ]
    snapshot_configs = [
        AppProtection.SnapshotConfig.Vmware(name="s1",
        restore_config=ref(restore_configs[0]), 
        policy=AppProtection.ProtectionPolicy("policy1", rule_name="rule_name"))
    ]
```