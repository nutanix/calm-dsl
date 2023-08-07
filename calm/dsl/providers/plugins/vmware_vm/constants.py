class VCENTER:

    VERSION = "v6"
    DATACENTER = "vmware/{}/datacenter".format(VERSION)
    TEMPLATE = "vmware/{}/template".format(VERSION)
    CONTENT_LIBRARY = "vmware/{}/library".format(VERSION)
    CONTENT_LIBRARY_TEMPLATE = "vmware/{}/library_items".format(VERSION)
    DATASTORE = "vmware/{}/datastore".format(VERSION)
    HOST = "vmware/{}/host".format(VERSION)
    CLUSTER = "vmware/{}/cluster".format(VERSION)
    STORAGE_POD = "vmware/{}/storage_pod".format(VERSION)
    NETWORK = "vmware/{}/network".format(VERSION)
    NETWORK_ADAPTER = "vmware/{}/network_adapter".format(VERSION)
    CUSTOMIZATION = "vmware/{}/customization".format(VERSION)
    TIMEZONE = "vmware/{}/timezone".format(VERSION)
    ACCOUNTS = "vmware/{}/accounts".format(VERSION)
    TEMPLATE_DEFS = ("vmware/{}/accounts/".format(VERSION)) + "{}/templates"
    FILE_PATHS = "vmware/{}/file_paths".format(VERSION)
    TAGS = "vmware/{}/vm_categories".format(VERSION)
    DATACENTER = "vmware/{}/datacenter".format(VERSION)
    POWER_STATE = {
        "POWER_ON": "poweron",
        "POWER_OFF": "poweroff",
        "ON": "ON",
        "OFF": "OFF",
    }

    DISK_ADAPTER_TYPES = {"SCSI": "SCSI", "IDE": "IDE", "SATA": "SATA"}

    DISK_TYPES = {"DISK": "disk", "CD-ROM": "cdrom"}

    DISK_ADAPTERS = {"disk": ["SCSI", "SATA"], "cdrom": ["IDE"]}

    DISK_MODE = {
        "Independent - Persistent": "independent_persistent",
        "Dependent": "persistent",
        "Independent - Nonpersistent": "independent_nonpersistent",
    }

    CONTROLLER = {
        "SCSI": {
            "Lsi Logic Parallel": "VirtualLsiLogicController",
            "Lsi Logic SAS": "VirtualLsiLogicSASController",
            "VMware Paravirtual": "ParaVirtualSCSIController",
            "Bus Logic Parallel": "VirtualBusLogicController",
        },
        "SATA": {"Virtual SATA Controller": "VirtualAHCIController"},
    }

    SCSIControllerOptions = {
        "VirtualLsiLogicController": "Lsi Logic Parallel",
        "VirtualLsiLogicSASController": "Lsi Logic SAS",
        "ParaVirtualSCSIController": "VMware Paravirtual",
        "VirtualBusLogicController": "Bus Logic Parallel",
    }

    SATAControllerOptions = {"VirtualAHCIController": "Virtual SATA Controller"}

    BUS_SHARING = {
        "No Sharing": "noSharing",
        "Virtual Sharing": "virtualSharing",
        "Physical Sharing": "physicalSharing",
    }

    KEY_BASE = {
        "CONTROLLER": {"SCSI": 1000, "SATA": 15000, "IDE": 200},
        "NETWORK": 4000,
        "DISK": 2000,
    }

    ControllerLimit = {"SCSI": 4, "SATA": 4, "IDE": 2}

    OperatingSystem = {"Linux": "GUEST_OS_LINUX", "Windows": "GUEST_OS_WINDOWS"}

    GuestCustomizationModes = {
        "Linux": ["Cloud Init", "Custom Spec", "Predefined Customization"],
        "Windows": ["Predefined Customization", "Custom Spec"],
    }

    VirtualControllerNameMap = {
        "vim.vm.device.VirtualIDEController": "VirtualIDEController",
        "vim.vm.device.VirtualLsiLogicSASController": "VirtualLsiLogicSASController",
        "vim.vm.device.VirtualSCSIController": "VirtualSCSIController",
        "vim.vm.device.VirtualSATAController": "VirtualSATAController",
        "vim.vm.device.ParaVirtualSCSIController": "ParaVirtualSCSIController",
        "vim.vm.device.VirtualAHCIController": "VirtualAHCIController",
        "vim.vm.device.VirtualBusLogicController": "VirtualBusLogicController",
        "vim.vm.device.VirtualLsiLogicController": "VirtualLsiLogicController",
    }

    ControllerMap = {
        "vim.vm.device.VirtualIDEController": "IDE",
        "vim.vm.device.VirtualLsiLogicSASController": "SCSI",
        "vim.vm.device.VirtualSCSIController": "SCSI",
        "vim.vm.device.VirtualSATAController": "SATA",
        "vim.vm.device.ParaVirtualSCSIController": "SCSI",
        "vim.vm.device.VirtualAHCIController": "SATA",
        "vim.vm.device.VirtualBusLogicController": "SCSI",
        "vim.vm.device.VirtualLsiLogicController": "SCSI",
    }

    ControllerDeviceSlotMap = {
        "VirtualIDEController": 2,
        "VirtualLsiLogicSASController": 16,
        "VirtualSCSIController": 16,
        "VirtualSATAController": 30,
        "ParaVirtualSCSIController": 16,
        "VirtualAHCIController": 30,
        "VirtualBusLogicController": 16,
        "VirtualLsiLogicController": 16,
    }

    NetworkAdapterMap = {
        "vim.vm.device.VirtualE1000": "e1000",
        "vim.vm.device.VirtualE1000e": "e1000e",
        "vim.vm.device.VirtualPCNet32": "pcnet32",
        "vim.vm.device.VirtualVmxnet": "vmxnet",
        "vim.vm.device.VirtualVmxnet2": "vmxnet2",
        "vim.vm.device.VirtualVmxnet3": "vmxnet3",
    }

    DiskMap = {
        "vim.vm.device.VirtualDisk": "disk",
        "vim.vm.device.VirtualCdrom": "cdrom",
    }
