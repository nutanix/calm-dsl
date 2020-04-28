from .entity import EntityType, Entity
from .validator import PropertyValidator


# Readiness Probe


class ReadinessProbeType(EntityType):
    __schema_name__ = "ReadinessProbe"
    __openapi_type__ = "app_readiness_probe"


class ReadinessProbeValidator(PropertyValidator, openapi_type="app_readiness_probe"):
    __default__ = None
    __kind__ = ReadinessProbeType

    @classmethod
    def validate(cls, value, is_array):
        entity_type = cls.__kind__

        if value is None:
            return
        elif isinstance(value, entity_type):
            pass
        elif isinstance(value, dict):
            entity_type.validate_dict(value)
        else:
            raise TypeError("{} is not a valid readiness probe".format(value))
    
    def compile(cls):

        cdict = super().compile()
        cred = cdict.pop("login_credential_local_reference", None)
        # If cred is not None, reset it again
        if cred:
            cdict["login_credential_local_reference"] = cred
        
        return cdict



def readiness_probe(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return ReadinessProbeType(name, bases, kwargs)


ReadinessProbe = readiness_probe()
