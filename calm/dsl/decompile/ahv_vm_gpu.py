import sys

from calm.dsl.decompile.render import render_template
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_ahv_vm_gpu(cls):

    gpu_vendor_key_map = {"AMD": "Amd", "INTEL": "Intel", "NVIDIA": "Nvidia"}
    gpu_mode_key_map = {
        "PASSTHROUGH_GRAPHICS": "passThroughGraphic",
        "PASSTHROUGH_COMPUTE": "passThroughCompute",
        "VIRTUAL": "virtual",
    }
    gpu_data = cls.get_dict()

    user_attrs = {}
    gpu_vendor = gpu_data["vendor"]
    if gpu_vendor_key_map.get(gpu_vendor, None):
        user_attrs["vendor_key"] = gpu_vendor_key_map[gpu_vendor]

    else:
        LOG.error("Unknown GPU vendor '{}'".format(gpu_vendor))
        sys.exit(-1)

    gpu_mode = gpu_data["mode"]
    if gpu_mode_key_map.get(gpu_mode, None):
        user_attrs["mode_key"] = gpu_mode_key_map[gpu_mode]

    else:
        LOG.error("Unknown GPU mode '{}'".format(gpu_mode))
        sys.exit(-1)

    user_attrs["device_id"] = gpu_data.get("device_id", 0)

    text = render_template(schema_file="ahv_vm_gpu.py.jinja2", obj=user_attrs)
    return text.strip()
