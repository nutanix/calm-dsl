from .entity import EntityType, Entity
from .validator import PropertyValidator


# AHV VM NIC


class AhvNicType(EntityType):
    __schema_name__ = "AhvNic"
    __openapi_type__ = "vm_ahv_nic"


class AhvNicValidator(PropertyValidator, openapi_type="vm_ahv_nic"):
    __default__ = None
    __kind__ = AhvNicType


def ahv_vm_nic(**kwargs):
    name = getattr(AhvNicType, "__schema_name__")
    bases = (Entity,)
    return AhvNicType(name, bases, kwargs)


AhvVmNic = ahv_vm_nic()


# AHV VM Vdisk


class AhvVdiskType(EntityType):
    __schema_name__ = "AhvVdisk"
    __openapi_type__ = "vm_ahv_vdisk"


class AhvVdiskValidator(PropertyValidator, openapi_type="vm_ahv_vdisk"):
    __default__ = None
    __kind__ = AhvVdiskType


def ahv_vm_vdisk(**kwargs):
    name = getattr(AhvVdiskType, "__schema_name__")
    bases = (Entity,)
    return AhvVdiskType(name, bases, kwargs)


AhvVmVdisk = ahv_vm_vdisk()


# AHV VM Disk


class AhvDiskType(EntityType):
    __schema_name__ = "AhvDisk"
    __openapi_type__ = "vm_ahv_disk"


class AhvDiskValidator(PropertyValidator, openapi_type="vm_ahv_disk"):
    __default__ = None
    __kind__ = AhvDiskType


def ahv_vm_disk(**kwargs):
    name = getattr(AhvDiskType, "__schema_name__")
    bases = (Entity,)
    return AhvDiskType(name, bases, kwargs)


AhvVmDisk = ahv_vm_disk()


# AHV VM Resources


class AhvVmResourcesType(EntityType):
    __schema_name__ = "AhvVmResources"
    __openapi_type__ = "vm_ahv_resources"


class AhvVmResourcesValidator(PropertyValidator, openapi_type="vm_ahv_resources"):
    __default__ = None
    __kind__ = AhvVmResourcesType


def ahv_vm_resources(**kwargs):
    name = getattr(AhvVmResourcesType, "__schema_name__")
    bases = (Entity,)
    return AhvVmResourcesType(name, bases, kwargs)


AhvVmResources = ahv_vm_resources()


# AHV VM


class AhvVmType(EntityType):
    __schema_name__ = "AhvVm"
    __openapi_type__ = "vm_ahv"


class AhvVmValidator(PropertyValidator, openapi_type="vm_ahv"):
    __default__ = None
    __kind__ = AhvVmType


def ahv_vm(**kwargs):
    name = getattr(AhvVmType, "__schema_name__")
    bases = (Entity,)
    return AhvVmType(name, bases, kwargs)


AhvVm = ahv_vm()
