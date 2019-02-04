import ast
import inspect
import textwrap
import json
from json import JSONEncoder
import tokenize
from io import StringIO
import os
import sys

import yaml
from jinja2 import Environment, PackageLoader
import asttokens
import jsonref



class EntityJSONEncoder(JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'json_repr'):
            return obj.json_repr()
        else:
            return super().default(obj)


template = Environment(loader=PackageLoader(__name__, 'schemas')).get_template('main.yaml.jinja2')

tdict = yaml.safe_load(StringIO(template.render()))

# Check if all references are resolved
tdict = jsonref.loads(json.dumps(tdict))
# print(json.dumps(tdict, cls=EntityJSONEncoder, indent=4, separators=(",", ": ")))

SCHEMAS = tdict["components"]["schemas"]



# Load v3 schema objects
# TODO - refactor

v3template = Environment(loader=PackageLoader(__name__, 'v3schemas')).get_template('main.yaml.jinja2')

v3tdict = yaml.safe_load(StringIO(v3template.render()))
v3tdict = jsonref.loads(json.dumps(v3tdict))
V3SCHEMAS = v3tdict["components"]["schemas"]


class BaseType:

    def __init__(self, default=None):
        self._default = default

    def __get__(self, instance, owner):
        return instance.__dict__[self.name] if instance else self._default

    def __validate__(self, value):
        pass

    def __set__(self, instance, value):
        self.__validate__(value)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class BaseListType(BaseType):

    def __validate__(self, value):
        super().__validate__(value)
        if not isinstance(value, list):
            raise TypeError('{} is not of type {}.'.format(value, list))


class EntityType(BaseType):

    def __init__(self, entity_type, default=None):
        super().__init__(default=default)
        self.entity_type = entity_type

    def __validate__(self, value):
        super().__validate__(value)
        if not isinstance(value, self.entity_type):
            raise TypeError('{} is not of type {}.'.format(value, self.entity_type))


class EntityListType(BaseListType):

    def __init__(self, entity_type, default=[]):
        super().__init__(default=default)
        self.entity_type = entity_type

    def __validate__(self, value):
        super().__validate__(value)
        for v in value:
            if not isinstance(v, self.entity_type):
                raise TypeError('{} is not of type {}.'.format(v, self.entity_type))


class StringType(EntityType):

    def __init__(self, default=''):
        super().__init__(str, default=default)


class StringListType(EntityListType):

    def __init__(self):
        super().__init__(str)


class IntType(EntityType):

    def __init__(self, default=0):
        super().__init__(int, default=default)


class NonNegativeIntType(IntType):

    def __validate__(self, value):
        super().__validate__(value)
        if value < 0:
            raise ValueError('Cannot be negative.')


class BoolType(EntityType):

    def __init__(self, default=False):
        super().__init__(bool, default=default)


class DictType(EntityType):

    def __init__(self, default={}):
        super().__init__(dict, default=default)


class PortType(EntityType):

    def __init__(self):
        super().__init__(Port)


class PortListType(EntityListType):

    def __init__(self):
        super().__init__(Port)


class ServiceType(EntityType):

    def __init__(self):
        super().__init__(Service)


class ServiceListType(EntityListType):

    def __init__(self):
        super().__init__(Service)


class SubstrateType(EntityType):

    def __init__(self):
        super().__init__(Substrate)


class SubstrateListType(EntityListType):

    def __init__(self):
        super().__init__(Substrate)


class DeploymentType(EntityType):

    def __init__(self):
        super().__init__(Deployment)


class DeploymentListType(EntityListType):

    def __init__(self):
        super().__init__(Deployment)


class ProfileType(EntityType):

    def __init__(self):
        super().__init__(Profile)


class ProfileListType(EntityListType):

    def __init__(self):
        super().__init__(Profile)



###


class EntityBase(type):

    def __new__(mcls, name, bases, ns):

        cls = super().__new__(mcls, name, bases, ns)

        cls._default_attrs = {}

        schema_props = cls.__schema__.get("properties", {})

        for attr, attr_props in schema_props.items():

            attr_type = attr_props.get("type", None)

            if attr_type is None:
                raise Exception("Invalid schema {} given".format(attr_props))

            if attr_type == "object" or attr_type == "array":
                attr_type = attr_props.get("x-calm-dsl-type", None)

                if attr_type is None:
                    raise Exception("calm dsl extension not found. Invalid schema {}"
                                    .format(attr_props))

            descriptor_cls = type_to_descriptor_cls.get(attr_type, None)
            if descriptor_cls is None:
                raise TypeError("Unknown type {} given".format(attr_type))

            setattr(cls, attr, descriptor_cls())

            # TODO - add right default based on attr_type/descriptor_cls
            cls._default_attrs[attr] = attr_props.get("default", None)

        cls._default_attrs["name"] = cls.__name__
        cls._default_attrs["description"] = cls.__doc__ if cls.__doc__ is not None else ''

        for k, v in cls.__dict__.items():
            func = getattr(v, '__set_name__', None)
            if func is not None:
                func(cls, k)

        for key in cls.attributes:
            if key not in cls._default_attrs.keys():
                raise KeyError("Unknown key {} given".format(key))

        return cls

    def __str__(cls):
        return cls.__name__


class Entity(metaclass=EntityBase):

    __schema__ = {}

    attributes = {}

    def __init__(self, **kwargs):

        self._all_attrs = {
            **self.__class__._default_attrs,
            **self.__class__.attributes,
            **kwargs,
        }

        for key, value in self._all_attrs.items():
            if key not in self.__class__._default_attrs.keys():
                raise KeyError("Unknown key {} given".format(key))
            setattr(self, key, value)

    def __str__(self):
        return str(self.__class__.__name__)

    def json_repr(self):
        return self._all_attrs

    def json_dumps(self, pprint=False, sort_keys=False):
        return json.dumps(self.json_repr(),
                          cls=EntityJSONEncoder,
                          sort_keys=sort_keys,
                          indent=4 if pprint else None,
                          separators=(",", ": ") if pprint else (",", ":")
        )


type_to_descriptor_cls = {

    "string": StringType,
    "strings": StringListType,

    "integer": IntType,

    "dict": DictType,

    "boolean": BoolType,

    "port": PortType,
    "ports": PortListType,

    "service": ServiceType,
    "services": ServiceListType,

    "substrate": SubstrateType,
    "substrates": SubstrateListType,

    "deployment": DeploymentType,
    "deployments": DeploymentListType,

    "profile": ProfileType,
    "profiles": ProfileListType,
}


class Port(Entity):

    __schema__ = SCHEMAS["Port"]



class Service(Entity):

    __schema__ = SCHEMAS["Service"]
    __v3_schema__ = V3SCHEMAS["Service"]


class Substrate(Entity):

    __schema__ = SCHEMAS["Substrate"]
    __v3_schema__ = V3SCHEMAS["Substrate"]


class Deployment(Entity):

    __schema__ = SCHEMAS["Deployment"]
    __v3_schema__ = V3SCHEMAS["DeploymentCreate"]


class Profile(Entity):

    __schema__ = SCHEMAS["Profile"]
    __v3_schema__ = V3SCHEMAS["Profile"]


class Blueprint(Entity):

    __schema__ = SCHEMAS["Blueprint"]
    __v3_schema__ = V3SCHEMAS["Blueprint"]



###


def read_vm_spec(filename):

    file_path = os.path.join(os.path.dirname(inspect.getfile(sys._getframe(1))), filename)

    with open(file_path, "r") as f:
        return yaml.safe_load(f.read())



###


def dump(name, obj, dct):
    code = inspect.getsource(type(obj))
    atok = asttokens.ASTTokens(code, parse=True)
    dct[name] = ASTtoDict(atok).visit(atok.tree)


def export_json(atok, pretty_print=False):

    dict = ASTtoDict(atok).visit(atok.tree)

    dict['comments'] = [{
        'ast_type': 'comment',
        'value': token.string,
        'start': token.startpos,
        'end': token.endpos,
        'loc': {
            'start': {
                'line': token.start[0],
                'column': token.start[1]
            },
            'end': {
                'line': token.end[0],
                'column': token.end[1]
            }
        }
    } for token in atok.tokens if token.type == tokenize.COMMENT]

    return json.dumps(
        dict,
        indent=4 if pretty_print else None,
        sort_keys=True,
        separators=(",", ": ") if pretty_print else (",", ":")
    )


class ASTtoDict:
    ast_type_field = "ast_type"

    def __init__(self, atok):
        self.atok = atok

    def visit(self, node):
        node_type = node.__class__.__name__
        meth = getattr(self, "visit_" + node_type, self.default_visit)
        return meth(node)

    def default_visit(self, node):
        node_type = node.__class__.__name__
        # Add node type
        args = {
            self.ast_type_field: node_type
        }
        # Visit fields
        for field in node._fields:
            assert field != self.ast_type_field
            meth = getattr(
                self, "visit_field_" + node_type + "_" + field,
                self.default_visit_field
            )
            args[field] = meth(getattr(node, field))
        # Visit attributes
        for attr in node._attributes:
            assert attr != self.ast_type_field
            meth = getattr(
                self, "visit_attribute_" + node_type + "_" + attr,
                self.default_visit_field
            )
            # Use None as default when lineno/col_offset are not set
            args[attr] = meth(getattr(node, attr, None))

        if hasattr(node, 'first_token'):
            args['start'] = node.first_token.startpos
            args['end'] = node.last_token.endpos

        args['source'] = self.atok.get_text(node)

        return args

    def default_visit_field(self, val):
        if isinstance(val, ast.AST):
            return self.visit(val)
        elif isinstance(val, list) or isinstance(val, tuple):
            return [self.visit(x) for x in val]
        else:
            return val

    # Special visitors
    def visit_NoneType(self, val):
        return None

    def visit_str(self, val):
        return val

    def visit_field_NameConstant_value(self, val):
        return str(val)

    def visit_Bytes(self, val):
        return str(val.s)

    def visit_field_Num_n(self, val):
        if isinstance(val, int):
            return {
                self.ast_type_field: "int",
                "n": str(val)
            }
        elif isinstance(val, float):
            return {
                self.ast_type_field: "float",
                "n": str(val)
            }
        elif isinstance(val, complex):
            return {
                self.ast_type_field: "complex",
                "n": str(val.real),
                "i": str(val.imag)
            }


def parse(source):
    assert (isinstance(source, str))

    atok = asttokens.ASTTokens(source, parse=True)

    return atok
