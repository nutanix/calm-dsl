import copy
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)
DSL_METADATA_MAP = {
    "Service": {},
    "Package": {},
    "Deployment": {},
    "Profile": {},
    "Substrate": {},
}
# TODO Check for credential


def update_dsl_metadata_map(entity_type, entity_name, entity_obj):
    global DSL_METADATA_MAP
    if entity_type not in DSL_METADATA_MAP:
        return

    DSL_METADATA_MAP[entity_type][entity_name] = entity_obj


def get_dsl_metadata_map(context=[]):
    global DSL_METADATA_MAP

    metadata = copy.deepcopy(DSL_METADATA_MAP)
    for c in context:
        if c in metadata:
            metadata = metadata[c]
        else:
            return

    return metadata


def init_dsl_metadata_map(metadata):
    global DSL_METADATA_MAP
    DSL_METADATA_MAP = metadata
