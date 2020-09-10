import os

from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import CalmVariable as Variable
from calm.dsl.builtins import CalmTask as Task
from calm.dsl.builtins import action, ref, basic_cred
from calm.dsl.builtins import read_local_file
from calm.dsl.builtins import vm_disk_package, AhvVmDisk, AhvVmNic
from calm.dsl.builtins import AhvVmGC, AhvVmResources, AhvVm
from calm.dsl.config import get_context


# SSH Credentials
CENTOS_USER = "centos"
CENTOS_KEY = read_local_file(os.path.join("keys", "centos"))
CENTOS_PUBLIC_KEY = read_local_file(os.path.join("keys", "centos_pub"))
CentosCred = basic_cred(
    CENTOS_USER, CENTOS_KEY, name="Centos", type="KEY", default=True
)

# OS Image details for VM
CENTOS_IMAGE_SOURCE = "http://download.nutanix.com/calm/CentOS-7-x86_64-1810.qcow2"
CentosPackage = vm_disk_package(
    name="centos_disk", config={"image": {"source": CENTOS_IMAGE_SOURCE}}
)


# ANIMAL (Base Service)


class AnimalService(Service):
    """Example animal service"""

    sound = Variable.Simple("NotImplemented")
    animal_var = Variable.Simple("Pet")

    @action
    def get_sound():
        """Example animal action"""
        Task.Exec.ssh(name="sound_name", script="echo @@{sound}@@")


class AnimalPackage(Package):
    """Sample Package"""

    # Services created by installing this Package
    services = [ref(AnimalService)]

    # Package Actions
    @action
    def __install__():

        # Step 1
        Task.Exec.ssh(
            name="Task1", filename=os.path.join("scripts", "pkg_install_task.sh")
        )

    @action
    def __uninstall__():

        # Step 1
        Task.Exec.ssh(
            name="Task1", filename=os.path.join("scripts", "pkg_uninstall_task.sh")
        )


class AnimalVmResources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [AhvVmDisk.Disk.Scsi.cloneFromVMDiskPackage(CentosPackage, bootable=True)]
    nics = [AhvVmNic.DirectNic.ingress("vlan.0")]

    guest_customization = AhvVmGC.CloudInit(
        config={
            "users": [
                {
                    "name": CENTOS_USER,
                    "ssh-authorized-keys": [CENTOS_PUBLIC_KEY],
                    "sudo": ["ALL=(ALL) NOPASSWD:ALL"],
                }
            ]
        }
    )


class AnimalVm(AhvVm):

    resources = AnimalVmResources


class AnimalSubstrate(Substrate):
    """AHV VM Substrate"""

    provider_spec = AnimalVm


class AnimalDeployment(Deployment):
    """Sample Deployment"""

    packages = [ref(AnimalPackage)]
    substrate = ref(AnimalSubstrate)


# DOG inherits ANIMAL


class DogService(AnimalService):

    dependencies = [ref(AnimalService)]
    sound = Variable.Simple("woof")
    dog_prop = Variable.Simple("loyal")

    @action
    def get_dog_props():
        """Example dog action"""
        Task.Exec.ssh(name="d1", script="echo @@{dog_prop}@@")


class DogPackage(AnimalPackage):

    services = [ref(DogService)]


class DogVmResources(AnimalVmResources):

    memory = 16
    vCPUs = 8


class DogVm(AnimalVm):

    resources = DogVmResources


class DogSubstrate(AnimalSubstrate):
    """AHV VM Substrate for Dog"""

    provider_spec = DogVm


class DogDeployment(AnimalDeployment):
    """Dog Deployment"""

    packages = [ref(DogPackage)]
    substrate = ref(DogSubstrate)


# HUSKY inherits DOG


class HuskyService(DogService):

    dependencies = [ref(DogService)]
    sound = Variable.Simple("howl")
    husky_prop = Variable.Simple("Siberian")

    @action
    def get_husky_props():
        """Example dog action"""
        Task.Exec.ssh(name="d1", script="echo @@{husky_prop}@@")


class HuskyPackage(DogPackage):

    services = [ref(HuskyService)]


class HuskySubstrate(DogSubstrate):
    """AHV VM Substrate for Husky"""

    pass


class HuskyDeployment(DogDeployment):
    """Husky Deployment"""

    packages = [ref(HuskyPackage)]
    substrate = ref(HuskySubstrate)


# CAT inherits ANIMAL


class CatService(AnimalService):

    dependencies = [ref(AnimalService)]
    sound = Variable.Simple("meow")


class CatPackage(AnimalPackage):

    services = [ref(CatService)]


class CatVmResources(AnimalVmResources):

    memory = 8
    vCPUs = 4


class CatVm(AnimalVm):

    resources = CatVmResources


class CatSubstrate(AnimalSubstrate):
    """AHV VM Substrate for Cat"""

    provider_spec = CatVm


class CatDeployment(AnimalDeployment):
    """Cat Deployment"""

    packages = [ref(CatPackage)]
    substrate = ref(CatSubstrate)


##


class Default(Profile):

    # Deployments under this profile
    deployments = [AnimalDeployment, DogDeployment, HuskyDeployment, CatDeployment]

    @action
    def get_all_sounds():
        AnimalService.get_sound(name="S1")
        DogService.get_sound(name="S2")
        HuskyService.get_sound(name="S3")
        CatService.get_sound(name="S4")


class TestInheritance(Blueprint):
    """Example blueprint to test inheritance"""

    credentials = [CentosCred]
    services = [AnimalService, DogService, CatService, HuskyService]
    packages = [CentosPackage, AnimalPackage, DogPackage, CatPackage, HuskyPackage]
    substrates = [AnimalSubstrate, DogSubstrate, CatSubstrate, HuskySubstrate]
    profiles = [Default]


def test_json():
    """Test the generated json for a single VM
    against known output"""
    import os

    # Resetting context
    ContextObj = get_context()
    ContextObj.reset_configuration()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "test_inheritance_bp_output.json")

    generated_json = TestInheritance.json_dumps(pprint=True)
    known_json = open(file_path).read()

    assert generated_json == known_json


def main():
    print(TestInheritance.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
