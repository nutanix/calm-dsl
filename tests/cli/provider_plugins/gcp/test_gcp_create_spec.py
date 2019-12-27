import pytest
from .. import plugin_test


@pytest.mark.slow
@pytest.mark.presetup_required
@plugin_test("GCP_VM")
class TestGCPSpec:
    def test_normal_spec(self):
        """
            VM OS: Linux
            Zone: Yes
            Root Disk: Yes
                Use Existing Disk: Yes
            Additional Disks: No
            Blank Disks: No
            Networks: No
            Ssh Keys: No
            Guest Customization: No
        """
        pass

    def test_vm_spec_having_additional_disks(self):
        """
            VM OS: Linux
            Zone: Yes
            Root Disk: Yes
                Use Existing Disk: Yes
            Additional Disks: Yes(5)
                Existing Disk: Yes(1)
                local-ssd: Yes(2)
                    Interface :
                        SCSI(1)
                        NVMe(1)
                pd-ssd: Yes(1)
                pd-standard: Yes(1)
            Blank Disks: No
            Networks: No
            Ssh Keys: No
            Guest Customization: No
        """
        pass
    
    def test_vm_spec_having_blank_disks(self):
        """
            VM OS: Linux
            Zone: Yes
            Root Disk: Yes
                Use Existing Disk: No
                Storage Type: pd-standard
            Additional Disks: No
            Blank Disks: Yes(2)
                pd-ssd: Yes(1)
                pd-standard: Yes(1)
            Networks: No
            Ssh Keys: No
            Guest Customization: No
        """
        pass
    
    def test_vm_spec_with_ssh_keys(self):
        """
            VM OS: Linux
            Zone: Yes
            Root Disk: Yes
                Use Existing Disk: No
                Storage Type: pd-ssd
            Additional Disks: No
            Blank Disks: No
            Networks: No
            Ssh Keys: Yes
            Guest Customization: No
        """
        pass
