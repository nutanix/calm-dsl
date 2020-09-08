import pytest
from .. import plugin_test


@pytest.mark.slow
@pytest.mark.presetup_required
@plugin_test("AWS_VM")
class TestAWSSpec:
    def test_normal_spec(self):
        """
        Not Having: instance types, region, user_data, tags added
        Custom Disks: No
        Custom Subnets: No(depends on VPC and regions)
        """
        pass

    def test_vm_spec_with_instance_type(self):
        """
        Having: instance type
        Not having: region, user_data, tags added
        Custom Disks: No
        Custom Subnets: No(depends on VPC and regions)
        """
        pass

    def test_vm_spec_with_region(self):
        """
        Having: instance type, region
        Not having: user_data, tags added, availabilty zone, machine image, IAM role
                    Key-PAIR, VPC
        Custom Disks: No
        Custom Subnets: No(depends on VPC)
        """
        pass

    def test_vm_spec_with_region_dependent_data(self):
        """
        Having: instance type, region, availabilty zone, machine image IAM role, Key-Pair, VPC, Security Group,
                 user_data, custom tags,
        Custom Disks: Yes
        Custom Subnets: Yes
        """
        pass
