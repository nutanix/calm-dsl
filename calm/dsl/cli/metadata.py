from calm.dsl.builtins import Metadata
from .utils import get_module_from_file


def get_metadata_module_from_file(dsl_file):
    """Returns module given a file (.py)"""

    return get_module_from_file("calm.dsl.user_metadata", dsl_file)


def get_metadata_class_from_module(user_module):
    """Returns project class given a module"""

    UserMetadata = None
    for item in dir(user_module):
        obj = getattr(user_module, item)
        if isinstance(obj, type(Metadata)):
            if obj.__bases__[0] == Metadata:
                UserMetadata = obj

    return UserMetadata


def get_metadata_payload(dsl_file):

    user_metadata_module = get_metadata_module_from_file(dsl_file)
    UserMetadata = get_metadata_class_from_module(user_metadata_module)
    if not UserMetadata:
        return {}

    payload = UserMetadata.get_dict()
    return payload
