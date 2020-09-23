from calm.dsl.builtins import AhvVmResourcesType

from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.ahv_vm_disk import render_ahv_vm_disk
from calm.dsl.decompile.ahv_vm_nic import render_ahv_vm_nic
from calm.dsl.decompile.ahv_vm_gc import render_ahv_vm_gc
from calm.dsl.decompile.ahv_vm_gpu import render_ahv_vm_gpu
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_ahv_vm_resources(cls, boot_config, vm_name_prefix=""):

    LOG.debug("Rendering {} ahv_vm_resources template".format(cls.__name__))
    if not isinstance(cls, AhvVmResourcesType):
        raise TypeError("{} is not of type {}".format(cls, AhvVmResourcesType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__

    # Memory to GiB
    user_attrs["memory"] = int(user_attrs["memory"]) // 1024

    disk_list = []
    for disk in cls.disks:
        disk_list.append(render_ahv_vm_disk(disk, boot_config))

    nic_list = []
    for nic in cls.nics:
        nic_list.append(render_ahv_vm_nic(nic))

    gpu_list = []
    for gpu in cls.gpus:
        gpu_list.append(render_ahv_vm_gpu(gpu))

    user_attrs.update(
        {
            "disks": ", ".join(disk_list),
            "nics": ", ".join(nic_list),
            "gpus": ", ".join(gpu_list),
        }
    )
    if getattr(cls, "guest_customization", None):
        user_attrs["guest_customization"] = render_ahv_vm_gc(
            cls.guest_customization, vm_name_prefix=vm_name_prefix
        )

    text = render_template(schema_file="ahv_vm_resources.py.jinja2", obj=user_attrs)
    return text.strip()
