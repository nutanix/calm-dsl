import pytest
from .. import plugin_test


@pytest.mark.slow
@pytest.mark.presetup_required
@plugin_test("AHV_VM")
class TestAHVSpec:
    def test_normal_spec(self):
        """
        Category: Yes
        Multiple Categories of same Family Check: No
        Disk Images: Yes
            DISK: 1
            CD-ROM: 1
        Virtual Disks: No
        Network Adapters: No
        Customization Script: No
        """
        pass

    def test_vm_spec_dup_category(self):
        """
        Category: Yes
        Multiple Categories of same Family Check: Yes
            (For every family, you can use single category)
        Disk Images: Yes
            DISK: 0
            CD-ROM: 1
        Virtual Disks: No
        Network Adapters: No
        Customization Script: No
        """
        pass

    def test_vm_spec_having_virtual_disks(self):
        """
        Category: Yes
        Multiple Categories of same Family Check: No
        Disk Images: Yes
            DISK: 0
            CD-ROM: 1
        Virtual Disks: Yes
            DISK: 1
            CD-ROM: 1
        Network Adapters: No
        Customization Script: No
        """
        pass

    def test_vm_spec_with_nic(self):
        """
        Category: Yes
        Multiple Categories of same Family Check: No
        Disk Images: Yes
            DISK: 0
            CD-ROM: 1
        Virtual Disks: No
        Network Adapters: Yes
        Customization Script: No
        """
        pass

    def test_vm_spec_with_cloud_init_gc(self):
        """
        Category: Yes
        Multiple Categories of same Family Check: No
        Disk Images: Yes
            DISK: 0
            CD-ROM: 1
        Virtual Disks: No
        Network Adapters: No
        Customization Script: Yes
            Customization Type = Cloud_Init
        """
        pass

    def test_vm_spec_with_sys_prep_gc(self, os_type="Windows"):
        """
        Category: Yes
        Multiple Categories of same Family Check: No
        Disk Images: Yes
            DISK: 0
            CD-ROM: 1
        Virtual Disks: No
        Network Adapters: No
        Customization Script: Yes
            Customization Type = sysprep
        """
        pass
