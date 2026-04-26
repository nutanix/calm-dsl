"""AHV VM Resources decompile renderer.

Whole-reference macro values (e.g. ``"@@{gc}@@"`` for guest_customization,
disks, nics, memory) are emitted as bare strings rather than being passed
through their normal renderers, which expect dict-shaped inputs.
"""

from calm.dsl.builtins import AhvVmResourcesType
from calm.dsl.builtins.models.macro_helper import has_macro

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

    # Convert memory from MiB back to GiB.
    # When memory is a macro string the value is already in DSL form; leave it as-is
    # so the Jinja2 template can quote it correctly.
    raw_memory = user_attrs["memory"]
    if has_macro(raw_memory):
        user_attrs["memory"] = raw_memory
    else:
        user_attrs["memory"] = int(raw_memory) // 1024

    disk_list = []
    for disk in cls.disks:
        # A string macro means the whole disk entry is runtime-resolved.
        if has_macro(disk):
            disk_list.append('"{}"'.format(disk))
        else:
            disk_list.append(render_ahv_vm_disk(disk, boot_config))

    nic_list = []
    for nic in cls.nics:
        # A string macro means the whole NIC entry is runtime-resolved.
        if has_macro(nic):
            nic_list.append('"{}"'.format(nic))
        else:
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
    gc = getattr(cls, "guest_customization", None)
    if gc:
        # FIX: guest_customization can be a whole-reference JSON variable macro
        # (e.g. "@@{gc}@@").  render_ahv_vm_gc calls cls.get_dict() and would
        # crash on a plain string.  Emit the macro pre-quoted for the template.
        if has_macro(gc):
            user_attrs["guest_customization"] = '"{}"'.format(gc)
        else:
            user_attrs["guest_customization"] = render_ahv_vm_gc(
                gc, vm_name_prefix=vm_name_prefix
            )

    user_attrs["boot_type"] = "LEGACY"  # default boot type is legacy
    if user_attrs.get("boot_config", {}):
        user_attrs["boot_type"] = user_attrs["boot_config"].get("boot_type", None)

    user_attrs["vtpm_enabled"] = False  # default vtpm enabled is False
    if user_attrs.get("vtpm_config", {}):
        user_attrs["vtpm_enabled"] = user_attrs["vtpm_config"].get(
            "vtpm_enabled", False
        )

    text = render_template(schema_file="ahv_vm_resources.py.jinja2", obj=user_attrs)
    return text.strip()
