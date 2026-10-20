"""Secure Boot payloads must use the Q35 machine type."""

import json
from unittest.mock import patch

import pytest

from calm.dsl.builtins import AhvVmDisk, ahv_vm_resources, read_ahv_spec
from calm.dsl.providers import get_provider


@pytest.mark.parametrize("calm_version", ["4.2.0", "4.4.0"])
def test_secure_boot_resources_select_q35_and_preserve_boot_disk(calm_version):
    Resources = ahv_vm_resources()
    BootDisk = AhvVmDisk.Disk.Scsi.allocateOnStorageContainer(1)
    BootDisk.bootable = True

    class SecureResources(Resources):
        boot_type = "SECURE_BOOT"
        disks = [BootDisk]

    with patch(
        "calm.dsl.store.version.Version.get_version", return_value=calm_version
    ), patch(
        "calm.dsl.builtins.models.ahv_vm_disk.common_helper.get_project_with_pc_account",
        return_value=({"name": "test-project"}, {"test-account": {}}),
    ):
        payload = json.loads(SecureResources.json_dumps())

    assert payload["machine_type"] == "Q35"
    assert payload["boot_config"] == {
        "boot_type": "SECURE_BOOT",
        "boot_device": {"disk_address": {"adapter_type": "SCSI", "device_index": 0}},
    }


@pytest.mark.parametrize("boot_type", ["LEGACY", "UEFI"])
def test_other_boot_types_do_not_select_q35(boot_type):
    Resources = ahv_vm_resources()

    class OtherResources(Resources):
        pass

    OtherResources.boot_type = boot_type
    with patch("calm.dsl.store.version.Version.get_version", return_value="4.4.0"):
        payload = json.loads(OtherResources.json_dumps())
    assert payload.get("machine_type") != "Q35"


@pytest.mark.parametrize("machine_type", [None, "PC", "Q35"])
def test_provider_spec_normalizes_secure_boot_machine_type(machine_type):
    spec = {
        "name": "secure-vm",
        "resources": {"boot_config": {"boot_type": "SECURE_BOOT"}},
    }
    if machine_type is not None:
        spec["resources"]["machine_type"] = machine_type
    get_provider("AHV_VM").validate_spec(spec)
    assert spec["resources"]["machine_type"] == "Q35"
    assert spec["resources"]["boot_config"]["boot_type"] == "SECURE_BOOT"


@pytest.mark.parametrize("boot_type", ["LEGACY", "UEFI"])
def test_provider_spec_preserves_machine_type_without_secure_boot(boot_type):
    spec = {
        "name": "other-vm",
        "resources": {"boot_config": {"boot_type": boot_type}, "machine_type": "PC"},
    }
    get_provider("AHV_VM").validate_spec(spec)
    assert spec["resources"]["machine_type"] == "PC"


def test_imported_ahv_spec_selects_q35(tmp_path):
    spec = {
        "name": "imported-vm",
        "resources": {"boot_config": {"boot_type": "SECURE_BOOT"}},
    }
    path = tmp_path / "secure-vm.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    provider_spec = read_ahv_spec(str(path))
    payload = provider_spec.__validate__("AHV_VM")
    assert payload["resources"]["machine_type"] == "Q35"
