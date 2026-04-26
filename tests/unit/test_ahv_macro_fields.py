"""
Unit tests for AHV substrate macro field support (spec section 3.2).

Verifies that the DSL compile path correctly handles Calm macro expressions
in every macro-capable AHV substrate field:

    Scalar (INT / string) fields
        vCPUs, cores_per_vCPU, memory_size_mib, disk_size_mib,
        disk image name (string inside cloneFromImageService),
        subnet UUID (string inside AhvVmNic),
        power_state, VM name

    JSON-object fields
        disk list entry (whole object replaced by macro string)
        NIC  list entry (whole object replaced by macro string)
        cluster reference (whole object replaced by macro string)

All tests mock Version.get_version() to return "4.4.0" so the version
guards inside AhvVmResourcesType.compile() do not abort.
"""

import json
import pytest
from unittest.mock import patch

from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVm
from calm.dsl.builtins import ahv_vm_resources, Ref
from calm.dsl.builtins.models.macro_helper import (
    has_macro,
    is_macro,
    validate_ahv_macro_fields,
)
from calm.dsl.constants import AHV_MACRO_FIELDS, MACRO_SUPPORT_AHV_SPEC_MIN_VERSION

AhvVmResources = ahv_vm_resources()

# ---------------------------------------------------------------------------
# Helper: compile a Resources class and return its JSON dict
# ---------------------------------------------------------------------------

_VERSION_PATCH = patch(
    "calm.dsl.builtins.models.ahv_vm.Version.get_version",
    return_value="4.4.0",
)


def _compile(resources_cls):
    """Return the compiled dict for the given AhvVmResources subclass."""
    with _VERSION_PATCH:
        return json.loads(resources_cls.json_dumps())


# ===========================================================================
# 1. macro_helper — unit tests for is_macro / has_macro
# ===========================================================================


class TestMacroHelper:
    """Tests for the macro detection utilities in macro_helper.py."""

    def test_is_macro_valid(self):
        assert is_macro("@@{cpu}@@") is True
        assert is_macro("@@{memory_gib}@@") is True
        assert is_macro("@@{my.var_1}@@") is True

    def test_is_macro_rejects_partial(self):
        assert is_macro("prefix_@@{cpu}@@") is False
        assert is_macro("@@{cpu}@@_suffix") is False
        assert is_macro("plain_string") is False

    def test_is_macro_non_string(self):
        assert is_macro(4) is False
        assert is_macro(None) is False
        assert is_macro(["@@{x}@@"]) is False
        assert is_macro({"k": "@@{x}@@"}) is False

    def test_has_macro_string(self):
        assert has_macro("@@{cpu}@@") is True
        assert has_macro("not_a_macro") is False

    def test_has_macro_list(self):
        assert has_macro(["@@{nic}@@"]) is True
        assert has_macro(["literal"]) is False
        assert has_macro([]) is False

    def test_has_macro_dict(self):
        assert has_macro({"uuid": "@@{cluster_uuid}@@"}) is True
        assert has_macro({"uuid": "abc-123", "kind": "cluster"}) is False

    def test_has_macro_non_string_scalar(self):
        assert has_macro(42) is False
        assert has_macro(None) is False


# ===========================================================================
# 1b. validate_ahv_macro_fields — allowlist enforcement
# ===========================================================================


class TestValidateAhvMacroFieldsAllowlist:
    """Covers the AHV macro-support allowlist contract for Calm 4.4.0+."""

    def test_constant_value(self):
        assert MACRO_SUPPORT_AHV_SPEC_MIN_VERSION == "4.4.0"

    def test_allowlist_exposes_expected_entities(self):
        assert set(AHV_MACRO_FIELDS.BY_ENTITY.keys()) == {
            "AhvVm",
            "AhvVmResources",
            "AhvDisk",
            "AhvNic",
        }

    def test_allowed_fields_pass(self):
        validate_ahv_macro_fields(
            {"name": "@@{vm}@@", "cluster_reference": "@@{c}@@"}, "AhvVm"
        )
        validate_ahv_macro_fields(
            {
                "memory_size_mib": "@@{m}@@",
                "num_sockets": "@@{s}@@",
                "num_vcpus_per_socket": "@@{v}@@",
                "power_state": "@@{p}@@",
                "guest_customization": "@@{gc}@@",
            },
            "AhvVmResources",
        )
        validate_ahv_macro_fields(
            {
                "data_source_reference": "@@{img}@@",
                "disk_size_mib": "@@{ds}@@",
            },
            "AhvDisk",
        )

    def test_disallowed_field_raises_sys_exit(self):
        with pytest.raises(SystemExit):
            validate_ahv_macro_fields({"description": "@@{desc}@@"}, "AhvVm")

    def test_disallowed_field_on_disk_raises(self):
        with pytest.raises(SystemExit):
            validate_ahv_macro_fields(
                {"device_properties": {"device_type": "@@{x}@@"}}, "AhvDisk"
            )

    def test_noop_on_non_mapping(self):
        validate_ahv_macro_fields(None, "AhvVm")
        validate_ahv_macro_fields("@@{whole_vm}@@", "AhvVm")
        validate_ahv_macro_fields([], "AhvVm")

    def test_unknown_entity_is_noop(self):
        validate_ahv_macro_fields({"anything": "@@{x}@@"}, "NotAnAhvEntity")


# ===========================================================================
# 2. Normal (literal) profile — sanity baseline
# ===========================================================================


class TestNormalProfileCompile:
    """Baseline: all literal values compile to correct numeric/string output."""

    class _Resources(AhvVmResources):
        memory = 4  # GiB
        vCPUs = 2
        cores_per_vCPU = 1
        power_state = "ON"
        boot_type = "LEGACY"
        disks = [AhvVmDisk.Disk.Scsi.cloneFromImageService("centos7", bootable=True)]
        nics = [AhvVmNic.NormalNic.ingress("subnet-uuid-1234")]

    def test_memory_converted_to_mib(self):
        cdict = _compile(self._Resources)
        assert cdict["memory_size_mib"] == 4 * 1024  # 4096

    def test_vcpus_literal(self):
        cdict = _compile(self._Resources)
        assert cdict["num_vcpus_per_socket"] == 2

    def test_cores_literal(self):
        cdict = _compile(self._Resources)
        assert cdict["num_sockets"] == 1

    def test_power_state_literal(self):
        cdict = _compile(self._Resources)
        assert cdict["power_state"] == "ON"

    def test_disk_image_name_literal(self):
        cdict = _compile(self._Resources)
        disk = cdict["disk_list"][0]
        assert disk["data_source_reference"]["name"] == "centos7"

    def test_nic_subnet_uuid_literal(self):
        cdict = _compile(self._Resources)
        nic = cdict["nic_list"][0]
        assert nic["subnet_reference"]["uuid"] == "subnet-uuid-1234"


# ===========================================================================
# 3. Scalar macro fields (INT and string)
# ===========================================================================


class TestScalarMacroFields:
    """Macros in INT-typed and string-typed substrate fields are preserved as-is."""

    class _Resources(AhvVmResources):
        memory = "@@{memory_mib}@@"
        vCPUs = "@@{vcpus}@@"
        cores_per_vCPU = "@@{cores}@@"
        power_state = "@@{power_state}@@"
        boot_type = "LEGACY"
        disks = [
            AhvVmDisk.Disk.Scsi.cloneFromImageService(
                "@@{img_name}@@",
                disk_size_mib="@@{disk_size_mib}@@",
                bootable=True,
            )
        ]
        nics = [AhvVmNic.NormalNic.ingress("@@{subnet_uuid}@@")]

    def test_memory_macro_not_converted(self):
        """Macro in memory must NOT be multiplied by 1024."""
        cdict = _compile(self._Resources)
        assert cdict["memory_size_mib"] == "@@{memory_mib}@@"

    def test_vcpus_macro_preserved(self):
        cdict = _compile(self._Resources)
        assert cdict["num_vcpus_per_socket"] == "@@{vcpus}@@"

    def test_cores_macro_preserved(self):
        cdict = _compile(self._Resources)
        assert cdict["num_sockets"] == "@@{cores}@@"

    def test_power_state_macro_preserved(self):
        cdict = _compile(self._Resources)
        assert cdict["power_state"] == "@@{power_state}@@"

    def test_disk_image_name_macro_preserved(self):
        cdict = _compile(self._Resources)
        disk = cdict["disk_list"][0]
        assert disk["data_source_reference"]["name"] == "@@{img_name}@@"

    def test_disk_size_macro_preserved(self):
        cdict = _compile(self._Resources)
        disk = cdict["disk_list"][0]
        assert disk["disk_size_mib"] == "@@{disk_size_mib}@@"

    def test_nic_subnet_uuid_macro_preserved(self):
        cdict = _compile(self._Resources)
        nic = cdict["nic_list"][0]
        assert nic["subnet_reference"]["uuid"] == "@@{subnet_uuid}@@"


# ===========================================================================
# 4. JSON-object macro fields (whole disk / NIC / cluster as macro string)
# ===========================================================================


class TestJsonObjectMacroFields:
    """
    A whole disk or NIC entry replaced by a bare macro string.
    The compile path must keep the string in the list as-is and
    skip adapter-index assignment / NIC validation for that entry.
    """

    class _Resources(AhvVmResources):
        memory = 4
        vCPUs = 2
        cores_per_vCPU = 1
        power_state = "ON"
        boot_type = "LEGACY"
        # Whole disk object replaced by macro
        disks = ["@@{disk}@@"]
        # Whole NIC object replaced by macro
        nics = ["@@{nic}@@"]

    def test_disk_macro_string_in_disk_list(self):
        """Macro string must appear unchanged in compiled disk_list."""
        cdict = _compile(self._Resources)
        assert cdict["disk_list"][0] == "@@{disk}@@"

    def test_nic_macro_string_in_nic_list(self):
        """Macro string must appear unchanged in compiled nic_list."""
        cdict = _compile(self._Resources)
        assert cdict["nic_list"][0] == "@@{nic}@@"

    def test_only_one_disk_entry(self):
        cdict = _compile(self._Resources)
        assert len(cdict["disk_list"]) == 1

    def test_only_one_nic_entry(self):
        cdict = _compile(self._Resources)
        assert len(cdict["nic_list"]) == 1


class TestClusterMacroField:
    """Cluster reference as a bare macro string on AhvVm."""

    class _VmResources(AhvVmResources):
        memory = 2
        vCPUs = 1
        cores_per_vCPU = 1
        boot_type = "LEGACY"
        disks = [AhvVmDisk.Disk.Scsi.cloneFromImageService("centos7")]
        nics = [AhvVmNic.NormalNic.ingress("subnet-uuid-1234")]

    class _Vm(AhvVm):
        name = "vm-test"
        resources = _VmResources
        cluster = "@@{cluster}@@"

    def test_cluster_macro_in_compiled_vm(self):
        with _VERSION_PATCH:
            cdict = json.loads(self._Vm.json_dumps())
        assert cdict["cluster_reference"] == "@@{cluster}@@"


# ===========================================================================
# 5. AllMacro — every macro-capable field at once
# ===========================================================================


class TestAllMacroFields:
    """All macro-capable fields set simultaneously; each must survive compile."""

    class _Resources(AhvVmResources):
        memory = "@@{memory_mib}@@"
        vCPUs = "@@{vcpus}@@"
        cores_per_vCPU = "@@{cores}@@"
        power_state = "@@{power_state}@@"
        boot_type = "LEGACY"
        disks = ["@@{disk}@@"]
        nics = ["@@{nic}@@"]

    class _Vm(AhvVm):
        name = "@@{vm_name}@@"
        resources = _Resources
        cluster = "@@{cluster}@@"

    def test_all_scalar_macros_preserved(self):
        cdict = _compile(self._Resources)
        assert cdict["memory_size_mib"] == "@@{memory_mib}@@"
        assert cdict["num_vcpus_per_socket"] == "@@{vcpus}@@"
        assert cdict["num_sockets"] == "@@{cores}@@"
        assert cdict["power_state"] == "@@{power_state}@@"

    def test_disk_and_nic_macros_preserved(self):
        cdict = _compile(self._Resources)
        assert cdict["disk_list"][0] == "@@{disk}@@"
        assert cdict["nic_list"][0] == "@@{nic}@@"

    def test_vm_name_and_cluster_macros_preserved(self):
        with _VERSION_PATCH:
            cdict = json.loads(self._Vm.json_dumps())
        assert cdict["name"] == "@@{vm_name}@@"
        assert cdict["cluster_reference"] == "@@{cluster}@@"


# ===========================================================================
# 6. Version guard — macro in memory on Calm < 4.4.0 must exit
# ===========================================================================


class TestVersionGuard:
    """Memory macro on a version below 4.4.0 must call sys.exit."""

    class _Resources(AhvVmResources):
        memory = "@@{memory_mib}@@"
        vCPUs = 2
        cores_per_vCPU = 1
        boot_type = "LEGACY"
        disks = [AhvVmDisk.Disk.Scsi.cloneFromImageService("centos7")]
        nics = [AhvVmNic.NormalNic.ingress("subnet-uuid")]

    def test_memory_macro_exits_on_old_calm(self):
        with patch(
            "calm.dsl.builtins.models.ahv_vm.Version.get_version",
            return_value="4.3.0",
        ):
            with pytest.raises(SystemExit):
                self._Resources.json_dumps()


# ===========================================================================
# 7. RunbookVariable — DICT guard
# ===========================================================================


class TestRunbookVariableDictGuard:
    """RunbookVariable.Simple.dictionary must raise NotImplementedError."""

    def test_dict_variable_raises(self):
        from calm.dsl.builtins.models.variable import RunbookVariable

        with pytest.raises(NotImplementedError) as exc_info:
            RunbookVariable.Simple.dictionary({"key": "value"}, name="cfg")

        assert "4.4.0" in str(exc_info.value)

    def test_string_variable_does_not_raise(self):
        from calm.dsl.builtins.models.variable import RunbookVariable

        # Should not raise
        var = RunbookVariable.Simple.string("hello", name="env", runtime=True)
        assert var is not None

    def test_int_variable_does_not_raise(self):
        from calm.dsl.builtins.models.variable import RunbookVariable

        var = RunbookVariable.Simple.int("2", name="vcpus", runtime=True)
        assert var is not None
