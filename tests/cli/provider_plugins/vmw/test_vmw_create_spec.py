import pytest
from .. import plugin_test


@pytest.mark.slow
@pytest.mark.presetup_required
@plugin_test("VMWARE_VM")
class TestVMWSpec:
    def test_vm_spec_with_drs_mode_off(self):
        """
        DRS Mode: No
        Template Defaults Editable : No
        Other SCSI controller: No
        Other SATA controller: No
        Other disks: No
        Other nics: No
        Guest_customization: No
        """
        pass

    def test_vm_spec_with_drs_mode_on(self):
        """
        DRS Mode: Yes
        Template Defaults Editable : No
        Other SCSI controller: No
        Other SATA controller: No
        Other disks: No
        Other nics: No
        Guest_customization: No
        """
        pass

    def test_vm_spec_editing_template_defaults(self):
        """
        DRS Mode: No
        Template Defaults Editable : Yes
        Other SCSI controller: No
        Other SATA controller: No
        Other disks: No
        Other nics: No
        Guest_customization: No
        """
        pass

    def test_vm_spec_with_custom_controllers(self):
        """
        DRS Mode: No
        Template Defaults Editable : No
        Other SCSI controller: Yes
        Other SATA controller: Yes
        Other disks: No
        Other nics: No
        Guest_customization: No
        """
        pass

    def test_vm_spec_having_custom_disks(self):
        """
        DRS Mode: No
        Template Defaults Editable : No
        Other SCSI controller: No
        Other SATA controller: No
        Other disks: Yes
        Other nics: No
        Guest_customization: No
        """
        pass

    def test_vm_spec_having_custom_nics(self):
        """
        DRS Mode: No
        Template Defaults Editable : No
        Other SCSI controller: No
        Other SATA controller: No
        Other disks: No
        Other nics: Yes
        Guest_customization: No
        """
        pass

    def test_vm_spec_having_cloud_init_linux_cus(self):
        """
        DRS Mode: No
        Template Defaults Editable : No
        Other SCSI controller: No
        Other SATA controller: No
        Other disks: No
        Other nics: No
        Guest_customization: Yes(OS = Linux)
            Type = Cloud Init
        """
        pass

    def test_vm_spec_having_custom_spec_linux_cus(self):
        """
        DRS Mode: No
        Template Defaults Editable : No
        Other SCSI controller: No
        Other SATA controller: No
        Other disks: No
        Other nics: No
        Guest_customization: Yes(OS = Linux)
            Type = Custom Spec
        """
        pass

    def test_vm_spec_having_predefined_linux_cus(self):
        """
        DRS Mode: No
        Template Defaults Editable : No
        Other SCSI controller: No
        Other SATA controller: No
        Other disks: No
        Other nics: No
        Guest_customization: Yes(OS = Linux)
            Type = Predefined Guest Customization
        """
        pass

    def test_vm_spec_having_predefined_windows_cus(self, os_type="Windows"):
        """
        DRS Mode: No
        Template Defaults Editable : No
        Other SCSI controller: No
        Other SATA controller: No
        Other disks: No
        Other nics: No
        Guest_customization: Yes(OS = Windows)
            Type = Predefined Guest Customization Name
        """
        pass

    def test_vm_spec_having_windows_guest_cus_with_domian(self, os_type="Windows"):
        """
        DRS Mode: No
        Template Defaults Editable : No
        Other SCSI controller: No
        Other SATA controller: No
        Other disks: No
        Other nics: No
        Guest_customization: Yes(OS = Windows)
            Type: Custom Spec
            Joining a domain: True
        """
        pass

    def test_vm_spec_having_windows_guest_cus_without_domian(self, os_type="Windows"):
        """
        DRS Mode: No
        Template Defaults Editable : No
        Other SCSI controller: No
        Other SATA controller: No
        Other disks: No
        Other nics: No
        Guest_customization: Yes(OS = Windows)
            Type: Custom Spec
            Joining a domain: False
        """
        pass
