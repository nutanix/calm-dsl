import importlib.util

from calm.dsl.builtins import Metadata

_Metadata = dict()


def get_metadata_module_from_file(dsl_file):
    """Returns module given a file (.py)"""

    module_name = "calm.dsl.user_metadata"
    spec = importlib.util.spec_from_file_location(module_name, dsl_file)
    user_module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(user_module)
    except SystemExit:
        # As some entities require metadata context. So absence of it will raise Error
        pass

    return user_module


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

    global _Metadata
    user_metadata_module = get_metadata_module_from_file(dsl_file)
    UserMetadata = get_metadata_class_from_module(user_metadata_module)
    if not UserMetadata:
        return {}

    payload = UserMetadata.get_dict()
    # updating global object
    _Metadata = payload
    return payload


def get_metadata_obj():
    return _Metadata
