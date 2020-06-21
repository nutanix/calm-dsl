import sys

from calm.dsl.decompile.render import render_template
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


def render_ahv_vm_gpu(cls):

    gpu_data = cls.get_dict()

    user_attrs = {}
    gpu_vendor = gpu_data["vendor"]
    if gpu_vendor == "AMD":
        user_attrs["vendor_key"] = "Amd"

    elif gpu_vendor == "INTEL":
        user_attrs["vendor_key"] = "Intel"

    elif gpu_vendor == "NVIDIA":
        user_attrs["vendor_key"] = "Nvidia"

    else:
        LOG.error("Unknown GPU vendor '{}'".format(gpu_vendor))
        sys.exit(-1)

    gpu_mode = gpu_data["mode"]
    if gpu_mode == "PASSTHROUGH_GRAPHICS":
        user_attrs["mode_key"] = "passThroughGraphic"

    elif gpu_mode == "PASSTHROUGH_COMPUTE":
        user_attrs["mode_key"] = "passThroughCompute"

    elif gpu_mode == "VIRTUAL":
        user_attrs["mode_key"] = "virtual"

    else:
        LOG.error("Unknown GPU mode '{}'".format(gpu_mode))
        sys.exit(-1)

    user_attrs["device_id"] = gpu_data.get("device_id", 0)

    text = render_template(schema_file="ahv_vm_gpu.py.jinja2", obj=user_attrs)
    return text.strip()
