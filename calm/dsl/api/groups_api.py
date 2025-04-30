from .resource import ResourceAPI
from .connection import REQUEST
from calm.dsl.constants import RESOURCE, MULTICONNECT, MULTIGROUP
from calm.dsl.api.connection import Connection


class MultiGroupsAPI:
    def __init__(self, connection):

        if isinstance(connection, Connection):
            self.pc_connection = connection
            self.ncm_connection = connection
        else:
            self.pc_connection = getattr(connection, MULTICONNECT.PC_OBJ)
            self.ncm_connection = getattr(connection, MULTICONNECT.NCM_OBJ)

        setattr(self, MULTIGROUP.PC_OBJ, GroupsAPI(self.pc_connection))
        setattr(self, MULTIGROUP.NCM_OBJ, GroupsAPI(self.ncm_connection))

    def get_pc_group_obj(self):
        return getattr(self, MULTIGROUP.PC_OBJ)

    def get_ncm_group_obj(self):
        return getattr(self, MULTIGROUP.NCM_OBJ)

    def create(self, payload):
        entity_type = payload.get("entity_type", "")

        try:
            if entity_type in RESOURCE.ENTITY.NCM:
                return self.get_ncm_group_obj().create(payload)
            elif entity_type in RESOURCE.ENTITY.NON_NCM:
                return self.get_pc_group_obj().create(payload)
            else:
                raise ValueError(
                    "Invalid entity_type '{}', should be one of {}".format(
                        entity_type, RESOURCE.ENTITY.NCM | RESOURCE.ENTITY.NON_NCM
                    )
                )
        except Exception as e:
            return None, e


class GroupsAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="groups")

    def create(self, payload):
        return self.connection._call(
            self.PREFIX,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )
