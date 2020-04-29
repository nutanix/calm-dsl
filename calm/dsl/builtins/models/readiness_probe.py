from .entity import EntityType, Entity
from .validator import PropertyValidator


# Readiness Probe


class ReadinessProbeType(EntityType):
    __schema_name__ = "ReadinessProbe"
    __openapi_type__ = "app_readiness_probe"

    def compile(cls):
        cdict = super().compile()
        cred = cdict.pop("login_credential_local_reference", None)
        # If cred is not None, reset it again
        if cred:
            cdict["login_credential_local_reference"] = cred

        return cdict


class ReadinessProbeValidator(PropertyValidator, openapi_type="app_readiness_probe"):
    __default__ = None
    __kind__ = ReadinessProbeType


def readiness_probe(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return ReadinessProbeType(name, bases, kwargs)


ReadinessProbe = readiness_probe()
