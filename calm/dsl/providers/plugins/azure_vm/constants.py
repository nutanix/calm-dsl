class AZURE:

    VERSION = "v1"
    URL = "azure_rm/{}".format(VERSION)
    AVAILABILTY_SETS = "{}/availability_sets".format(URL)
    AVAILABILITY_ZONES = "{}/availability_zones".format(URL)
    SECURITY_GROUPS = "{}/security_groups".format(URL)
    VIRTUAL_NETWORKS = "{}/virtual_networks".format(URL)
    SUBNETS = "{}/subnets".format(URL)
    RESOURCE_GROUPS = "{}/resource_groups".format(URL)
    LOCATIONS = "{}/locations".format(URL)
    VM_SIZES = "{}/vm_sizes".format(URL)
    IMAGE_PUBLISHERS = "{}/image_publishers".format(URL)
    IMAGE_OFFERS = "{}/image_offers".format(URL)
    IMAGE_SKUS = "{}/image_skus".format(URL)
    IMAGE_VERSIONS = "{}/image_versions".format(URL)
    SUBSCRIPTION_IMAGES = "{}/subscription_images".format(URL)
    SUBSCRIPTIONS = "{}/subscriptions".format(URL)
    IMAGES = "{}/images".format(URL)

    UNATTENDED_SETTINGS = ["FirstLogonCommands", "AutoLogon"]
    PROTOCOLS = {"HTTP": "Http", "HTTPS": "Https"}
    OPERATING_SYSTEMS = ["Linux", "Windows"]
    CACHE_TYPES = {"None": "None", "Read Write": "ReadWrite", "Write Only": "WriteOnly"}
    STORAGE_TYPES = {"Standard": "Standard_LRS", "Premium": "Premium_LRS"}
    DISK_CREATE_OPTIONS = {
        "ATTACH": "Attach",
        "EMPTY": "Empty",
        "FROMIMAGE": "FromImage",
    }
    ALLOCATION_METHODS = ["Dynamic", "Static"]
