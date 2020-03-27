"""
Calm DSL .NEXT demo

"""

from calm.dsl.builtins import (
    ref,
    basic_cred,
    secret_cred,
    CalmVariable,
    CalmTask,
    action,
)
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_provider_spec, read_local_file, read_spec

CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")
DNS_SERVER = read_local_file(".tests/dns_server")

project_spec = read_spec("specs/project_spec.json")
accounts = project_spec["project_detail"]["resources"]["account_reference_list"]


class Service1(Service):
    """Sample service"""


class Package1(Package):
    """Sample package """

    services = [ref(Service1)]


class Substrate1(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[0]["uuid"]


class Deployment1(Deployment):
    """Sample deployment"""

    packages = [ref(Package1)]
    substrate = ref(Substrate1)



class Service2(Service):
    """Sample service"""


class Package2(Package):
    """Sample package """

    services = [ref(Service2)]


class Substrate2(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[1]["uuid"]


class Deployment2(Deployment):
    """Sample deployment"""

    packages = [ref(Package2)]
    substrate = ref(Substrate2)


class Service3(Service):
    """Sample service"""


class Package3(Package):
    """Sample package """

    services = [ref(Service3)]


class Substrate3(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[2]["uuid"]


class Deployment3(Deployment):
    """Sample deployment"""

    packages = [ref(Package3)]
    substrate = ref(Substrate3)


class Service4(Service):
    """Sample service"""


class Package4(Package):
    """Sample package """

    services = [ref(Service4)]


class Substrate4(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[3]["uuid"]


class Deployment4(Deployment):
    """Sample deployment"""

    packages = [ref(Package4)]
    substrate = ref(Substrate4)


class Service5(Service):
    """Sample service"""


class Package5(Package):
    """Sample package """

    services = [ref(Service5)]


class Substrate5(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[4]["uuid"]


class Deployment5(Deployment):
    """Sample deployment"""

    packages = [ref(Package5)]
    substrate = ref(Substrate5)


class Service6(Service):
    """Sample service"""


class Package6(Package):
    """Sample package """

    services = [ref(Service6)]


class Substrate6(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[5]["uuid"]


class Deployment6(Deployment):
    """Sample deployment"""

    packages = [ref(Package6)]
    substrate = ref(Substrate6)


class Service7(Service):
    """Sample service"""


class Package7(Package):
    """Sample package """

    services = [ref(Service7)]


class Substrate7(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[6]["uuid"]


class Deployment7(Deployment):
    """Sample deployment"""

    packages = [ref(Package7)]
    substrate = ref(Substrate7)


class Service8(Service):
    """Sample service"""


class Package8(Package):
    """Sample package """

    services = [ref(Service8)]


class Substrate8(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[7]["uuid"]


class Deployment8(Deployment):
    """Sample deployment"""

    packages = [ref(Package8)]
    substrate = ref(Substrate8)


class Service9(Service):
    """Sample service"""


class Package9(Package):
    """Sample package """

    services = [ref(Service9)]


class Substrate9(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[8]["uuid"]


class Deployment9(Deployment):
    """Sample deployment"""

    packages = [ref(Package9)]
    substrate = ref(Substrate9)


class Service10(Service):
    """Sample service"""


class Package10(Package):
    """Sample package """

    services = [ref(Service10)]


class Substrate10(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[9]["uuid"]


class Deployment10(Deployment):
    """Sample deployment"""

    packages = [ref(Package10)]
    substrate = ref(Substrate10)


class Service11(Service):
    """Sample service"""


class Package11(Package):
    """Sample package """

    services = [ref(Service11)]


class Substrate11(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[10]["uuid"]


class Deployment11(Deployment):
    """Sample deployment"""

    packages = [ref(Package11)]
    substrate = ref(Substrate11)


class Service12(Service):
    """Sample service"""


class Package12(Package):
    """Sample package """

    services = [ref(Service12)]


class Substrate12(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[11]["uuid"]


class Deployment12(Deployment):
    """Sample deployment"""

    packages = [ref(Package12)]
    substrate = ref(Substrate12)


class Service13(Service):
    """Sample service"""


class Package13(Package):
    """Sample package """

    services = [ref(Service13)]


class Substrate13(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[12]["uuid"]


class Deployment13(Deployment):
    """Sample deployment"""

    packages = [ref(Package13)]
    substrate = ref(Substrate13)


class Service14(Service):
    """Sample service"""


class Package14(Package):
    """Sample package """

    services = [ref(Service14)]


class Substrate14(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[13]["uuid"]


class Deployment14(Deployment):
    """Sample deployment"""

    packages = [ref(Package14)]
    substrate = ref(Substrate14)


class Service15(Service):
    """Sample service"""


class Package15(Package):
    """Sample package """

    services = [ref(Service15)]


class Substrate15(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[14]["uuid"]


class Deployment15(Deployment):
    """Sample deployment"""

    packages = [ref(Package15)]
    substrate = ref(Substrate15)


class Service16(Service):
    """Sample service"""


class Package16(Package):
    """Sample package """

    services = [ref(Service16)]


class Substrate16(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[15]["uuid"]


class Deployment16(Deployment):
    """Sample deployment"""

    packages = [ref(Package16)]
    substrate = ref(Substrate16)


class Service17(Service):
    """Sample service"""


class Package17(Package):
    """Sample package """

    services = [ref(Service17)]


class Substrate17(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[16]["uuid"]


class Deployment17(Deployment):
    """Sample deployment"""

    packages = [ref(Package17)]
    substrate = ref(Substrate17)


class Service18(Service):
    """Sample service"""


class Package18(Package):
    """Sample package """

    services = [ref(Service18)]


class Substrate18(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[17]["uuid"]


class Deployment18(Deployment):
    """Sample deployment"""

    packages = [ref(Package18)]
    substrate = ref(Substrate18)


class Service19(Service):
    """Sample service"""


class Package19(Package):
    """Sample package """

    services = [ref(Service19)]


class Substrate19(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[18]["uuid"]


class Deployment19(Deployment):
    """Sample deployment"""

    packages = [ref(Package19)]
    substrate = ref(Substrate19)


class Service20(Service):
    """Sample service"""


class Package20(Package):
    """Sample package """

    services = [ref(Service20)]


class Substrate20(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[19]["uuid"]


class Deployment20(Deployment):
    """Sample deployment"""

    packages = [ref(Package20)]
    substrate = ref(Substrate20)


class Service21(Service):
    """Sample service"""


class Package21(Package):
    """Sample package """

    services = [ref(Service21)]


class Substrate21(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[20]["uuid"]


class Deployment21(Deployment):
    """Sample deployment"""

    packages = [ref(Package21)]
    substrate = ref(Substrate21)


class Service22(Service):
    """Sample service"""


class Package22(Package):
    """Sample package """

    services = [ref(Service22)]


class Substrate22(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[21]["uuid"]


class Deployment22(Deployment):
    """Sample deployment"""

    packages = [ref(Package22)]
    substrate = ref(Substrate22)


class Service23(Service):
    """Sample service"""


class Package23(Package):
    """Sample package """

    services = [ref(Service23)]


class Substrate23(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[22]["uuid"]


class Deployment23(Deployment):
    """Sample deployment"""

    packages = [ref(Package23)]
    substrate = ref(Substrate23)


class Service24(Service):
    """Sample service"""


class Package24(Package):
    """Sample package """

    services = [ref(Service24)]


class Substrate24(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[23]["uuid"]


class Deployment24(Deployment):
    """Sample deployment"""

    packages = [ref(Package24)]
    substrate = ref(Substrate24)


class Service25(Service):
    """Sample service"""


class Package25(Package):
    """Sample package """

    services = [ref(Service25)]


class Substrate25(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[24]["uuid"]


class Deployment25(Deployment):
    """Sample deployment"""

    packages = [ref(Package25)]
    substrate = ref(Substrate25)


class Service26(Service):
    """Sample service"""


class Package26(Package):
    """Sample package """

    services = [ref(Service26)]


class Substrate26(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[25]["uuid"]


class Deployment26(Deployment):
    """Sample deployment"""

    packages = [ref(Package26)]
    substrate = ref(Substrate26)


class Service27(Service):
    """Sample service"""


class Package27(Package):
    """Sample package """

    services = [ref(Service27)]


class Substrate27(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[26]["uuid"]


class Deployment27(Deployment):
    """Sample deployment"""

    packages = [ref(Package27)]
    substrate = ref(Substrate27)


class Service28(Service):
    """Sample service"""


class Package28(Package):
    """Sample package """

    services = [ref(Service28)]


class Substrate28(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[27]["uuid"]


class Deployment28(Deployment):
    """Sample deployment"""

    packages = [ref(Package28)]
    substrate = ref(Substrate28)


class Service29(Service):
    """Sample service"""


class Package29(Package):
    """Sample package """

    services = [ref(Service29)]


class Substrate29(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[28]["uuid"]


class Deployment29(Deployment):
    """Sample deployment"""

    packages = [ref(Package29)]
    substrate = ref(Substrate29)


class Service30(Service):
    """Sample service"""


class Package30(Package):
    """Sample package """

    services = [ref(Service30)]


class Substrate30(Substrate):
    """Sample substrate"""

    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("specs/provider_spec.yaml")
    provider_spec.spec["resources"][
        "account_uuid"
    ] = accounts[29]["uuid"]


class Deployment30(Deployment):
    """Sample deployment"""

    packages = [ref(Package30)]
    substrate = ref(Substrate30)


class DefaultProfile(Profile):
    """Sample application profile with variables"""

    deployments = [
        Deployment1,
        Deployment2,
        Deployment3,
        Deployment4,
        Deployment5,
        Deployment6,
        Deployment7,
        Deployment8,
        Deployment9,
        Deployment10,
        Deployment11,
        Deployment12,
        Deployment13,
        Deployment14,
        Deployment15,
        Deployment16,
        Deployment17,
        Deployment18,
        Deployment19,
        Deployment20,
        Deployment21,
        Deployment22,
        Deployment23,
        Deployment24,
        Deployment25,
        Deployment26,
        Deployment27,
        Deployment28,
        Deployment29,
        Deployment30,
    ]


class Blueprint1(Blueprint):

    credentials = [
        basic_cred("root", "password", default=True),
    ]

    services = [
        Service1,
        Service2,
        Service3,
        Service4,
        Service5,
        Service6,
        Service7,
        Service8,
        Service9,
        Service10,
        Service11,
        Service12,
        Service13,
        Service14,
        Service15,
        Service16,
        Service17,
        Service18,
        Service19,
        Service20,
        Service21,
        Service22,
        Service23,
        Service24,
        Service25,
        Service26,
        Service27,
        Service28,
        Service29,
        Service30,
    ]
    packages = [
        Package1,
        Package2,
        Package3,
        Package4,
        Package5,
        Package6,
        Package7,
        Package8,
        Package9,
        Package10,
        Package11,
        Package12,
        Package13,
        Package14,
        Package15,
        Package16,
        Package17,
        Package18,
        Package19,
        Package20,
        Package21,
        Package22,
        Package23,
        Package24,
        Package25,
        Package26,
        Package27,
        Package28,
        Package29,
        Package30,
    ]
    substrates = [
        Substrate1,
        Substrate2,
        Substrate3,
        Substrate4,
        Substrate5,
        Substrate6,
        Substrate7,
        Substrate8,
        Substrate9,
        Substrate10,
        Substrate11,
        Substrate12,
        Substrate13,
        Substrate14,
        Substrate15,
        Substrate16,
        Substrate17,
        Substrate18,
        Substrate19,
        Substrate20,
        Substrate21,
        Substrate22,
        Substrate23,
        Substrate24,
        Substrate25,
        Substrate26,
        Substrate27,
        Substrate28,
        Substrate29,
        Substrate30,
    ]

    profiles = [DefaultProfile]

n = 25

# update blueprint deployments
Blueprint1.profiles[0].deployments = Blueprint1.profiles[0].deployments[:n]

# update services, packages, substrates
Blueprint1.services = Blueprint1.services[:n]
Blueprint1.packages = Blueprint1.packages[:n]
Blueprint1.substrates = Blueprint1.substrates[:n]


"""
def get_updated_blueprint():

    n = 25

    # update blueprint deployments
    Blueprint1.profiles[0].deployments = Blueprint1.profiles[0].deployments[:n]

    # update services, packages, substrates
    Blueprint1.services = Blueprint1.services[:n]
    Blueprint1.packages = Blueprint1.packages[:n]
    Blueprint1.substrates = Blueprint1.substrates[:n]

    return Blueprint1
"""
