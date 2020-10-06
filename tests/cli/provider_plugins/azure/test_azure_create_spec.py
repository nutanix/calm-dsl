import pytest
from .. import plugin_test


@pytest.mark.slow
@pytest.mark.presetup_required
@plugin_test("AZURE_VM")
class TestAZURESpec:
    def test_normal_spec(self):
        """
        VM OS: Linux
        Availability Set: No
        Secrets : No
        Use custom Image for VM Image: No
        Nics: No
        Data disks: No
        """
        pass

    def test_spec_with_availability_set(self):
        """
        VM OS: Linux
        Availability Set: Yes
        Secrets : No
        Use custom Image for VM Image: No
        Nics: No
        Data disks: No
        """
        pass

    def test_spec_linux_os_with_secrets(self):
        """
        VM OS: Linux
        Availability Set: No
        Secrets : Yes
        Use custom Image for VM Image: No
        Nics: No
        Data disks: No
        """
        pass

    def test_spec_having_vm_custom_image(self):
        """
        VM OS: Linux
        Availability Set: No
        Secrets : No
        Use custom Image for VM Image: Yes
        Nics: No
        Data disks: No
        Disk create option for Os disk: FromImage
        """
        pass

    def test_spec_having_nics(self):
        """
        VM OS: Linux
        Availability Set: No
        Secrets : No
        Use custom Image for VM Image: No
        Nics: Yes(2)
        Data disks: No
        """
        pass

    def test_spec_having_data_disks(self):
        """
        VM OS: Linux
        Availability Set: No
        Secrets : No
        Use custom Image for VM Image: No
        Nics: No
        Data disks: Yes
        """
        pass

    def test_spec_having_tags(self):
        """
        VM OS: Linux
        Availability Set: No
        Secrets : No
        Use custom Image for VM Image: No
        Nics: No
        Tags: Yes(2)
        """
        pass

    def test_spec_having_windows_os_with_gc(self, os_type="Windows"):
        """
        VM OS: Windows
        Availability Set: No
        Secrets : No
        Use custom Image for VM Image: No
        Nics: No
        Guest Customization: Yes(Windows)
        """
        pass
