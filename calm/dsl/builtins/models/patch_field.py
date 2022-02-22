import sys

from calm.dsl.log import get_logging_handle
from .entity import EntityType, Entity
from .config_attrs import patch_data_field, ahv_nic_ruleset, ahv_disk_ruleset
from .validator import PropertyValidator

LOG = get_logging_handle(__name__)


class PatchField:
    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class Ahv:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        class vcpu:
            def __new__(
                cls, value="0", operation="equal", max_val=0, min_val=0, editable=False
            ):
                return _data_field_create(value, operation, max_val, min_val, editable)

        class memory:
            def __new__(
                cls, value="0", operation="equal", max_val=0, min_val=0, editable=False
            ):
                return _data_field_create(value, operation, max_val, min_val, editable)

        class numsocket:
            def __new__(
                cls, value="0", operation="equal", max_val=0, min_val=0, editable=False
            ):
                return _data_field_create(value, operation, max_val, min_val, editable)

        class Nics:
            def __new__(cls, *args, **kwargs):
                raise TypeError("'{}' is not callable".format(cls.__name__))

            class add:
                def __new__(cls, nic_value, editable=False):
                    return _nic_create(nic_value, editable)

            class delete:
                def __new__(cls, index=0, editable=False):
                    return _nic_operation(index, editable, "delete")

        class Disks:
            def __new__(cls, *args, **kwargs):
                raise TypeError("'{}' is not callable".format(cls.__name__))

            class add:
                def __new__(cls, disk_value, editable=False):
                    return _disk_create(disk_value, editable)

            class delete:
                def __new__(cls, index=0):
                    return _disk_operation(index, False, "delete")

            class modify:
                def __new__(
                    cls,
                    index=0,
                    editable=False,
                    value="0",
                    operation="equal",
                    max_val=0,
                    min_val=0,
                ):
                    return _disk_operation(
                        index, editable, "modify", operation, value, min_val, max_val
                    )

        class Category:
            def __new__(cls, *args, **kwargs):
                raise TypeError("'{}' is not callable".format(cls.__name__))

            class add:
                def __new__(cls, data):
                    val = []
                    for k in data:
                        val.append("{}:{}".format(k, data[k]))
                    return {"operation": "add", "val": val}

            class delete:
                def __new__(cls, data):
                    val = []
                    for k in data:
                        val.append("{}:{}".format(k, data[k]))
                    return {"operation": "delete", "val": val}


def _data_field_create(value, operation, max_val, min_val, editable):
    kwargs = {
        "value": value,
        "operation": operation,
        "max_value": max_val,
        "min_value": min_val,
        "editable": editable,
    }

    return patch_data_field(**kwargs)


def _nic_create(nic_value, editable):
    kwargs = {
        "nic_value": nic_value,
        "editable": editable,
        "operation": "add",
    }
    return ahv_nic_ruleset(**kwargs)


def _nic_operation(index, editable, operation):
    kwargs = {
        "index": str(index),
        "editable": editable,
        "operation": operation,
    }
    return ahv_nic_ruleset(**kwargs)


def _disk_operation(
    index, editable, disk_operation, operation="", value=0, min_val=0, max_val=0
):
    kwargs = {
        "index": index,
        "editable": editable,
        "operation": operation,
        "disk_operation": disk_operation,
        "value": str(value),
        "max_value": max_val,
        "min_value": min_val,
    }
    return ahv_disk_ruleset(**kwargs)


def _disk_create(disk_value, editable):
    kwargs = {
        "disk_value": disk_value,
        "editable": editable,
        "disk_operation": "add",
        "operation": "equal",
    }
    return ahv_disk_ruleset(**kwargs)
