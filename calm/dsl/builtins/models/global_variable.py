import sys

from .entity import EntityType
from .validator import PropertyValidator
from .variable import VariableType

from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class GlobalVariableType(EntityType):
    __schema_name__ = "GlobalVariable"
    __openapi_type__ = "global_variable"

    @classmethod
    def decompile(mcls, cdict, context=[], prefix=""):
        project_reference_list = cdict.pop("project_reference_list", [])
        gv_dict = {
            "definition": cdict,
            "project_reference_list": project_reference_list,
        }

        return super().decompile(gv_dict, context, prefix)


class GlobalVariableValidator(PropertyValidator, openapi_type="global_variable"):
    __default__ = None
    __kind__ = GlobalVariableType


class GlobalVariable:
    def __new__(
        cls,
        definition=None,
        projects=None,
    ):
        if definition is None:
            LOG.error("Variable definition cannot be None")
            sys.exit("Variable definition cannot be None")
        if not isinstance(definition, VariableType):
            LOG.error("Variable definition must be an instance of CalmVariable")
            sys.exit("Variable definition must be an instance of CalmVariable")
        kwargs = {"definition": definition, "projects": projects or []}
        return GlobalVariableType(definition.name, (GlobalVariable,), kwargs)
