Supports addition of action in patch configs (update configs) for AHV using `AhvUpdateConfigAttrs` class. For further details about this class refer [here](../../../release-notes/3.3.0/README.md#ahvupdateconfigattrs)

#### Example
```python
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
        PatchField.Ahv.Disks.delete(index=1),
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

    @action
    def app_edit_action_first():
        Task.Exec.escript(name="Task1", script="print 'Hello!'")
        Task.Exec.escript(name="Task2", script="print 'Hello2!'")
        Task.Exec.escript(name="Task3", script="print 'Hello3!'")
```

Note: only sequential tasks are supported in action.