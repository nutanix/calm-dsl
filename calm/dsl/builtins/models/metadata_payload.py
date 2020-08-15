# NOTE This module is not added to `builtins.__init__` bczit is only for dsl internal logics not for making blueprints
#       Below helpers are used in both `calm/dsl/cli/` and `calm/dsl/builtins/`
#       Import its helpers using `from calm.dsl.builtins.models.metadata_payload import *`

from .metadata import Metadata
from calm.dsl.tools import get_module_from_file

_MetadataPayload = dict()


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

    global _MetadataPayload
    user_metadata_module = get_metadata_module_from_file(dsl_file)
    UserMetadata = get_metadata_class_from_module(user_metadata_module)

    payload = {}
    if UserMetadata:
        payload = UserMetadata.get_dict()

    # updating global object
    _MetadataPayload = payload
    return payload


def get_metadata_obj():
    return _MetadataPayload
