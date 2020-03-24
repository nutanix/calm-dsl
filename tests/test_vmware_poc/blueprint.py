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
from calm.dsl.builtins import read_provider_spec, read_local_file

CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")
DNS_SERVER = read_local_file(".tests/dns_server")


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
    ] = "b817eafd-274f-ed67-163e-25254d92b406"


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
    ] = "64484c9c-d210-467a-ee99-1914a2e51609"


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
    ] = "dd27bbf0-125b-980c-05d9-658369feb1db"


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
    ] = "c148b537-0db9-8003-bdba-105a83a9405b"


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
    ] = "8f58c850-0335-01ef-d1e3-80c8721afbed"


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
    ] = "d1c269b4-b3b9-e894-d4ce-9d61f029f3e3"


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
    ] = "8e2cd42d-56d3-20ef-1ba5-c5d6c94ce419"


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
    ] = "65a40a83-f95a-ec5b-060e-2bec31428e8a"


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
    ] = "8baf8921-1dea-edbe-284d-e67a0aeee17e"


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
    ] = "9011c9ea-5772-9254-e33d-3cf7d64ae9bd"


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
    ] = "fc6824a6-da5b-bc45-a27a-2bcdc3885d3c"


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
    ] = "70693c18-1753-d541-35f3-3e359571ed26"


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
    ] = "ca0cc214-1ef4-e34c-d41d-9a5471edefe8"


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
    ] = "94096b6d-235c-a170-cd78-e2153d89d97c"


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
    ] = "866aeec7-78d2-0a3c-5bae-5e15da2051d6"


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
    ] = "617c5d80-d528-733c-7e92-21c3bf97b36d"


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
    ] = "cb72fe11-8ba5-5c18-c8aa-32a1ddec9f83"


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
    ] = "5aa280a6-c0c3-ab48-8eb9-da28874f41a9"


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
    ] = "e4dd2bfe-f6c5-1063-f86c-70160841d393"


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
    ] = "ac5b86c3-3097-f896-a114-c49a35d951d9"


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
    ] = "d262a20d-9950-b618-8088-d8bb6cb73fb0"


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
    ] = "08e0ee08-0ec9-76c9-d60a-79e9556258ba"


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
    ] = "3b202c8a-9549-f968-e754-cc646110fbcd"


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
    ] = "07bb798f-02c2-3fbd-4863-c2ac6bb2e921"


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
    ] = "ce98a7a9-af4c-d32c-2472-7ac2742f6480"


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
    ] = "f6e29e49-77b2-c543-1464-70fffd04ec2a"


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
    ] = "22e85995-560f-cc51-1bb2-c89f411f1965"


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
    ] = "af40cd40-67d1-952e-8a93-26729217585c"


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
    ] = "3af9f3fc-3776-c426-409b-8569c862be42"


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
    ] = "486cf689-78f1-aced-09ae-e1a05b04a38f"


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
