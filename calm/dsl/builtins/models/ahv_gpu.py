from .ahv_vm import ahv_vm_gpu


# AHV GPU


def create_ahv_gpu(vendor="", mode="", device_id=""):

    kwargs = {"vendor": vendor, "mode": mode, "device_id": device_id}

    return ahv_vm_gpu(**kwargs)


def amd_gpu_pass_through_graphic_mode(device_id=""):
    return create_ahv_gpu(
        vendor="AMD", mode="PASSTHROUGH_GRAPHICS", device_id=device_id
    )


def amd_gpu_pass_through_compute_mode(device_id=""):
    return create_ahv_gpu(vendor="AMD", mode="PASSTHROUGH_COMPUTE", device_id=device_id)


def amd_gpu_virtual_mode(device_id=""):
    return create_ahv_gpu(vendor="AMD", mode="VIRTUAL", device_id=device_id)


def intel_gpu_pass_through_graphic_mode(device_id=""):
    return create_ahv_gpu(
        vendor="INTEL", mode="PASSTHROUGH_GRAPHICS", device_id=device_id
    )


def intel_gpu_pass_through_compute_mode(device_id=""):
    return create_ahv_gpu(
        vendor="INTEL", mode="PASSTHROUGH_COMPUTE", device_id=device_id
    )


def intel_gpu_virtual_mode(device_id=""):
    return create_ahv_gpu(vendor="INTEL", mode="VIRTUAL", device_id=device_id)


def nvidia_gpu_pass_through_graphic_mode(device_id=""):
    return create_ahv_gpu(
        vendor="NVIDIA", mode="PASSTHROUGH_GRAPHICS", device_id=device_id
    )


def nvidia_gpu_pass_through_compute_mode(device_id=""):
    return create_ahv_gpu(
        vendor="NVIDIA", mode="PASSTHROUGH_COMPUTE", device_id=device_id
    )


def nvidia_gpu_virtual_mode(device_id=""):
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
