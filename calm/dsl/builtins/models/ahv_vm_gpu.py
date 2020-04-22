from .entity import EntityType, Entity
from .validator import PropertyValidator


# AHV GPU


class AhvGpuType(EntityType):
    __schema_name__ = "AhvGpu"
    __openapi_type__ = "vm_ahv_gpu"


class AhvGpuValidator(PropertyValidator, openapi_type="vm_ahv_gpu"):
    __default__ = None
    __kind__ = AhvGpuType


def ahv_vm_gpu(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AhvGpuType(name, bases, kwargs)


def create_ahv_gpu(vendor="", mode="", device_id=-1):

    kwargs = {"vendor": vendor, "mode": mode, "device_id": device_id}

    return ahv_vm_gpu(**kwargs)


def amd_gpu_pass_through_graphic_mode(device_id=-1):
    return create_ahv_gpu(
        vendor="AMD", mode="PASSTHROUGH_GRAPHICS", device_id=device_id
    )


def amd_gpu_pass_through_compute_mode(device_id=-1):
    return create_ahv_gpu(vendor="AMD", mode="PASSTHROUGH_COMPUTE", device_id=device_id)


def amd_gpu_virtual_mode(device_id=-1):
    return create_ahv_gpu(vendor="AMD", mode="VIRTUAL", device_id=device_id)


def intel_gpu_pass_through_graphic_mode(device_id=-1):
    return create_ahv_gpu(
        vendor="INTEL", mode="PASSTHROUGH_GRAPHICS", device_id=device_id
    )


def intel_gpu_pass_through_compute_mode(device_id=-1):
    return create_ahv_gpu(
        vendor="INTEL", mode="PASSTHROUGH_COMPUTE", device_id=device_id
    )


def intel_gpu_virtual_mode(device_id=-1):
    return create_ahv_gpu(vendor="INTEL", mode="VIRTUAL", device_id=device_id)


def nvidia_gpu_pass_through_graphic_mode(device_id=-1):
    return create_ahv_gpu(
        vendor="NVIDIA", mode="PASSTHROUGH_GRAPHICS", device_id=device_id
    )


def nvidia_gpu_pass_through_compute_mode(device_id=-1):
    return create_ahv_gpu(
        vendor="NVIDIA", mode="PASSTHROUGH_COMPUTE", device_id=device_id
    )


def nvidia_gpu_virtual_mode(device_id=-1):
    return create_ahv_gpu(vendor="NVIDIA", mode="VIRTUAL", device_id=device_id)


class AhvVmGpu:
    class Amd:

        passThroughGraphic = amd_gpu_pass_through_graphic_mode
        passThroughCompute = amd_gpu_pass_through_compute_mode
        virtual = amd_gpu_virtual_mode

    class Intel:

        passThroughGraphic = intel_gpu_pass_through_graphic_mode
        passThroughCompute = intel_gpu_pass_through_compute_mode
        virtual = intel_gpu_virtual_mode

    class Nvidia:

        passThroughGraphic = nvidia_gpu_pass_through_graphic_mode
        passThroughCompute = nvidia_gpu_pass_through_compute_mode
        virtual = nvidia_gpu_virtual_mode
