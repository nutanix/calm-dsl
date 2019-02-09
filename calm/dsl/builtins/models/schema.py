""" Schema should be according to OpenAPI 3 format with x-calm-dsl-type extension"""

import json
from io import StringIO

import yaml
from jinja2 import Environment, PackageLoader
import jsonref

from .validator import get_property_validators


_SCHEMAS = None


def get_all_schemas():
    global _SCHEMAS
    if not _SCHEMAS:
        _SCHEMAS = _load_all_schemas()
    return _SCHEMAS


def _load_all_schemas(schema_file='main.yaml.jinja2'):

    loader = PackageLoader(__name__, 'schemas')
    env = Environment(loader=loader)
    template = env.get_template(schema_file)

    tdict = yaml.safe_load(StringIO(template.render()))

    # Check if all references are resolved
    tdict = jsonref.loads(json.dumps(tdict))
    # print(json.dumps(tdict, cls=EntityJSONEncoder, indent=4, separators=(",", ": ")))

    schema = tdict["components"]["schemas"]
    return schema


def get_schema(name):
    schemas = get_all_schemas()
    return schemas.get(name, {})


def get_schema_props(name):
    schema = get_schema(name)
    return schema.get("properties", {})


def get_validator_type(schema_props, name):

    is_array = False

    if not schema_props:
        return None

    props = schema_props.get(name, None)
    if props is None:
        raise Exception("Invalid schema {} given".format(props))

    type_ = props.get("type", None)
    if type_ is None:
        raise Exception("Invalid schema {} given".format(schem_props))

    if type_ == "object":
        type_ = props.get("x-calm-dsl-type", None)
        if type_ is None:
            raise Exception(
                "x-calm-dsl-type extension for {} not found".format(name))

    if type_ == "array":
        item_props = props.get("items", None)
        item_type = item_props.get("type", None)
        if item_type is None:
            raise Exception("Invalid schema {} given".format(item_props))

        # TODO - refactor
        if item_type == "object":
            item_type = item_props.get("x-calm-dsl-type", None)
            if item_type is None:
                raise Exception(
                    "x-calm-dsl-type extension for {} not found".format(name))

        type_ = item_type
        is_array = True

    property_validators = get_property_validators()
    ValidatorType = property_validators.get(type_, None)
    if ValidatorType is None:
        raise TypeError("Type {} not supported".format(type_))

    return ValidatorType, is_array
