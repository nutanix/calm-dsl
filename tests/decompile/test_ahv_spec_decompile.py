import json

from calm.dsl.builtins import AhvVmType
from calm.dsl.builtins import read_spec, read_local_file
from calm.dsl.decompile.ahv_vm_disk import render_ahv_vm_disk
from calm.dsl.decompile.ahv_vm_nic import render_ahv_vm_nic
from calm.dsl.decompile.ahv_vm_gc import render_ahv_vm_gc
from calm.dsl.decompile.ahv_vm_gpu import render_ahv_vm_gpu
from calm.dsl.decompile.ahv_vm_resources import render_ahv_vm_resources
from calm.dsl.decompile.ahv_vm import render_ahv_vm
from calm.dsl.store import Cache
from calm.dsl.constants import CACHE

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
CENTOS_HM = DSL_CONFIG["AHV"]["IMAGES"]["DISK"]["CENTOS_HADOOP_MASTER"]
CENTOS_CI = DSL_CONFIG["AHV"]["IMAGES"]["DISK"]["CENTOS_7_CLOUD_INIT"]
SQL_SERVER_IMAGE = DSL_CONFIG["AHV"]["IMAGES"]["CD_ROM"]["SQL_SERVER_2014_x64"]
NETWORK1 = DSL_CONFIG["AHV"]["NETWORK"]["VLAN1211"]  # TODO change network constants

# projects
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]

NTNX_ACCOUNT = PROJECT["ACCOUNTS"]["NUTANIX_PC"][0]
NTNX_ACCOUNT_NAME = PROJECT["ACCOUNTS"]["NUTANIX_PC"][0]["NAME"]
NTNX_ACCOUNT_UUID = PROJECT["ACCOUNTS"]["NUTANIX_PC"][0]["UUID"]


image_cache_data = Cache.get_entity_data(
    entity_type=CACHE.ENTITY.AHV_DISK_IMAGE,
    name=CENTOS_HM,
    image_type="DISK_IMAGE",
    account_uuid=NTNX_ACCOUNT_UUID,
)
CENTOS_HM_UUID = image_cache_data.get("uuid", "")

image_cache_data = Cache.get_entity_data(
    entity_type=CACHE.ENTITY.AHV_DISK_IMAGE,
    name=CENTOS_CI,
    image_type="DISK_IMAGE",
    account_uuid=NTNX_ACCOUNT_UUID,
)
CENTOS_CI_UUID = image_cache_data.get("uuid", "")

image_cache_data = Cache.get_entity_data(
    entity_type=CACHE.ENTITY.AHV_DISK_IMAGE,
    name=SQL_SERVER_IMAGE,
    image_type="ISO_IMAGE",
    account_uuid=NTNX_ACCOUNT_UUID,
)
SQL_SERVER_IMAGE_UUID = image_cache_data.get("uuid", "")

subnet_cache_data = Cache.get_entity_data(
    entity_type=CACHE.ENTITY.AHV_SUBNET,
    name=NETWORK1,
    account_uuid=NTNX_ACCOUNT_UUID,
)
NETWORK1_UUID = subnet_cache_data.get("uuid", "")


def test_decompile():

    spec = read_spec("ahv_spec.json")

    # Correct nic uuids
    for nic in spec["resources"]["nic_list"]:
        nic["subnet_reference"]["name"] = NETWORK1
        nic["subnet_reference"]["uuid"] = NETWORK1_UUID

    disk_list = spec["resources"]["disk_list"]
    disk_list[0]["data_source_reference"]["name"] = CENTOS_HM
    disk_list[0]["data_source_reference"]["uuid"] = CENTOS_HM_UUID

    disk_list[1]["data_source_reference"]["name"] = SQL_SERVER_IMAGE
    disk_list[1]["data_source_reference"]["uuid"] = SQL_SERVER_IMAGE_UUID

    disk_list[2]["data_source_reference"]["name"] = SQL_SERVER_IMAGE
    disk_list[2]["data_source_reference"]["uuid"] = SQL_SERVER_IMAGE_UUID

    disk_list[3]["data_source_reference"]["name"] = SQL_SERVER_IMAGE
    disk_list[3]["data_source_reference"]["uuid"] = SQL_SERVER_IMAGE_UUID

    disk_list[4]["data_source_reference"]["name"] = CENTOS_CI
    disk_list[4]["data_source_reference"]["uuid"] = CENTOS_CI_UUID

    boot_config = spec["resources"].get("boot_config", {})
    vm_cls = AhvVmType.decompile(spec)
    print(render_ahv_vm(vm_cls, boot_config))

    vm_resources = vm_cls.resources
    print(render_ahv_vm_resources(vm_resources, boot_config=boot_config))

    # Get rendered disks
    for disk in vm_resources.disks:
        print(render_ahv_vm_disk(disk, boot_config))

    for nic in vm_resources.nics:
        print(render_ahv_vm_nic(nic))

    # TODO take care of generating file
    guest_customization_str = render_ahv_vm_gc(
        vm_resources.guest_customization, vm_name_prefix="vm_test"
    )
    print(guest_customization_str)

    for gpu in vm_resources.gpus:
        print(render_ahv_vm_gpu(gpu))
