""" Schema should be according to OpenAPI 3 format with x-calm-dsl-type extension"""

import json
from copy import deepcopy
from io import StringIO

from ruamel import yaml
from jinja2 import Environment, PackageLoader
import jsonref
from bidict import bidict

from .validator import get_property_validators
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)
_SCHEMAS = None


def _get_all_schemas():
    global _SCHEMAS
    if not _SCHEMAS:
        _SCHEMAS = _load_all_schemas()
    return _SCHEMAS


def _load_all_schemas(schema_file="main.yaml.jinja2"):

    loader = PackageLoader(__name__, "schemas")
    env = Environment(loader=loader)
    template = env.get_template(schema_file)

    tdict = yaml.safe_load(StringIO(template.render()))

    # Check if all references are resolved
    tdict = jsonref.loads(json.dumps(tdict))
    # print(json.dumps(tdict, cls=EntityJSONEncoder, indent=4, separators=(",", ": ")))

    schemas = tdict["components"]["schemas"]
    return schemas


def get_schema(name):

    schemas = _get_all_schemas()
    schema = schemas.get(name, None)
    if not schema:
        LOG.debug("Schema name can be one of {}".format(list(schema.keys())))
        raise TypeError("Invalid schema name {} given".format(name))

    return schema


def get_schema_props(name):
    schema = get_schema(name)
    schema_props = schema.get("properties", None)
    schema_type = schema.get("x-calm-dsl-type", None)
    if schema_type == "app_descriptor":
        schema_props = {}
    elif schema_type == "app_provider_spec":
        schema_props = {}
    elif not schema_props:
        LOG.debug("Schema properties for schema {} is not available".format(name))
        raise TypeError("Invalid schema name {} given".format(name))

    return schema_props


def get_validator_details(schema_props, name):

    object_type = False
    is_array = False
    object_validators = {}
    object_defaults = {}
    object_display_map = {}

    props = schema_props.get(name, None)
    if props is None:
        raise Exception("Invalid schema {} given".format(props))

    type_ = props.get("type", None)
    if type_ is None:
        raise Exception("Invalid schema {} given".format(schema_props))

    if type_ == "object":
        type_ = props.get("x-calm-dsl-type", None)
        if type_ is None:
            raise Exception("x-calm-dsl-type extension for {} not found".format(name))
        elif type_ == "object":
            object_type = True
            for name in props.get("properties", {}):
                validator, is_array, default = get_validator_details(
                    props["properties"], name
                )
                attr_name = props["properties"][name].get(
                    "x-calm-dsl-display-name", name
                )
                object_validators[attr_name] = (validator, is_array)
                object_defaults[attr_name] = default
                object_display_map[attr_name] = name

    if type_ == "array":
        item_props = props.get("items", None)
        item_type = item_props.get("type", None)
        if item_type is None:
            LOG.debug("Item type not found in schema {}".format(item_props))
            raise Exception("Invalid schema {} given".format(item_props))

        ValidatorType, _, _ = get_validator_details(props, "items")
        return ValidatorType, True, list

    property_validators = get_property_validators()
    ValidatorType = property_validators.get(type_, None)
    if object_type:
        ValidatorType = ValidatorType.__kind__(
            object_validators, object_defaults, object_display_map
        )
    if ValidatorType is None:
        raise TypeError("Type {} not supported".format(type_))

    # Get default from schema if given, else set default from validator type
    class NotDefined:
        pass

    default = None
    schema_default = props.get("default", NotDefined)
    if schema_default is NotDefined:
        class_default = ValidatorType.get_default(is_array)
        default = class_default
    else:
        default = lambda: deepcopy(schema_default)  # noqa: E731

    return ValidatorType, is_array, default


def get_validators_with_defaults(schema_props):

    validators = {}
    defaults = {}
    display_map = bidict()
    for name, props in schema_props.items():
        ValidatorType, is_array, default = get_validator_details(schema_props, name)
        attr_name = props.get("x-calm-dsl-display-name", name)
        validators[attr_name] = (ValidatorType, is_array)
        defaults[attr_name] = default
        display_map[attr_name] = name

    return validators, defaults, display_map


def get_schema_details(schema_name):

    schema_props = get_schema_props(schema_name)
    validators, defaults, display_map = get_validators_with_defaults(schema_props)

    return schema_props, validators, defaults, display_map
