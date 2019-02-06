import ast
import inspect
import textwrap
import json
from json import JSONEncoder
import tokenize
from io import StringIO
import os
import sys
from collections import OrderedDict

import yaml
from jinja2 import Environment, PackageLoader
import asttokens
import jsonref


class EntityJSONEncoder(JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'json_repr'):
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


# TODO - separate validators into separate classes.

class EntityType:

    def __init__(self, entity_type, default=None, is_array=False, **kwargs):
        self.entity_type = entity_type
        self._default = default
        self.is_array = is_array

    def __default__(self):
        return self._default

    def __get__(self, instance, owner):
        return instance.__dict__[self.name] if instance else self._default

    def __validate_item__(self, value):
        if not isinstance(value, self.entity_type):
            raise TypeError('{} is not of type {}.'.format(value, self.entity_type))

    def __validate_list__(self, values):
        if not isinstance(values, list):
            raise TypeError('{} is not of type {}.'.format(values, list))

    def __validate__(self, value, is_array=False):
        if not self.is_array:
            self.__validate_item__(value)
        else:
            self.__validate_list__(value)
            for v in value:
                self.__validate_item__(v)

    def __set__(self, instance, value):
        self.__validate__(value)
        instance.__dict__[self.name] = value # This will not work for class objects

    def __set_name__(self, owner, name):
        self.name = name


class StringType(EntityType):

    def __init__(self, **kwargs):
        super().__init__(str, default='', **kwargs)


class StringListType(StringType):

    def __init__(self, **kwargs):
        super().__init__(is_array=True, **kwargs)


class IntType(EntityType):

    def __init__(self, **kwargs):
        super().__init__(int, default=0, **kwargs)


class NonNegativeIntType(IntType):

    def __validate__(self, value):
        super().__validate__(value)
        if value < 0:
            raise ValueError('Cannot be negative.')


class BoolType(EntityType):

    def __init__(self, **kwargs):
        super().__init__(bool, default=False, **kwargs)


class DictType(EntityType):

    def __init__(self, **kwargs):
        super().__init__(dict, default={}, **kwargs)


class PortType(EntityType):

    def __init__(self, **kwargs):
        super().__init__(Port, **kwargs)


class PortListType(PortType):

    def __init__(self, **kwargs):
        super().__init__(is_array=True, **kwargs)


class ServiceType(EntityType):

    def __init__(self, **kwargs):
        super().__init__(Service, **kwargs)


class ServiceListType(ServiceType):

    def __init__(self, **kwargs):
        super().__init__(is_array=True, **kwargs)


class SubstrateType(EntityType):

    def __init__(self, **kwargs):
        super().__init__(Substrate, **kwargs)


class SubstrateListType(SubstrateType):

    def __init__(self, **kwargs):
        super().__init__(is_array=True, **kwargs)


class DeploymentType(EntityType):

    def __init__(self, **kwargs):
        super().__init__(Deployment, **kwargs)


class DeploymentListType(DeploymentType):

    def __init__(self, **kwargs):
        super().__init__(is_array=True, **kwargs)


class ProfileType(EntityType):

    def __init__(self, **kwargs):
        super().__init__(Profile, **kwargs)


class ProfileListType(ProfileType):

    def __init__(self, **kwargs):
        super().__init__(is_array=True, **kwargs)

###

class CustomDict(dict):
    pass


class EntityBase(type):

    @classmethod
    def __prepare__(mcls, name, bases, **kwargs):
        return CustomDict()

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

            DescriptorType = type_to_descriptor_cls.get(attr_type, None)
            if DescriptorType is None:
                raise TypeError("Unknown type {} given".format(attr_type))

            desc = DescriptorType()
            setattr(cls, attr, desc)

            cls._default_attrs[attr] = attr_props.get("default", desc.__default__())

        cls._default_attrs["name"] = cls.__name__
        cls._default_attrs["description"] = cls.__doc__ if cls.__doc__ is not None else ''

        # __set_name__() is called right after class creation which in this case happens
        # in the super() call above. [PEP 487]
        # Call __set_name__() again to set the right attribute names
        for k, v in cls.__dict__.items():
            func = getattr(v, '__set_name__', None)
            if func is not None:
                func(cls, k)

        # Check if any spurious class attibutes are given before class creation
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
                          separators=(",", ": ") if pprint else (",", ":"))


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


"""
Note:
Descriptors do not work on metaclass as class attributes are stored
as `mappingproxy` objects. This makes `class.__dict__` read-only, so only
`class.__setattr__` remains as an avenue for setting class attributes.
But, `setattr` works by looking for a data descriptor in
`type(obj).__mro__`. If a data descriptor is found, it calls
`__set__` and exits.
As `class.__dict__` cannot used to set attribute. `setattr` is the only way.
This causes infinite recursion!


"""

class FooDict(OrderedDict):

    def __init__(self):
        self.valid_attrs = ["singleton"]

    def __setitem__(self, name, value):

        if not (name.startswith('__') and name.endswith('__')):
            if name not in self.valid_attrs:
                raise TypeError("Unknown attribute {} given".format(name))

        super().__setitem__(name, value)


class FooBase(type):

    @classmethod
    def __prepare__(mcls, name, bases, **kwargs):
        return FooDict()

    def __new__(mcls, name, bases, foodict):

        # Replace foodict to dict() before passing to super()
        cls = type.__new__(mcls, name, bases, dict(foodict))

        cls.__valid_attrs__ = foodict.valid_attrs

        setattr(type(cls), "singleton", BoolType())

        print(mcls.__dict__)

        for k, v in mcls.__dict__.items():
            func = getattr(v, '__set_name__', None)
            if func is not None:
                func(mcls, k)

        return cls

    def __setattr__(cls, name, value):
        print("{}->{}".format(name, value))

        if not (name.startswith('__') and name.endswith('__')):

            if not name in cls.__valid_attrs__:
                raise TypeError("Unknown attribute {} given".format(name))

            descr_obj = cls.__class__.__dict__.get(name, None)

            func = getattr(descr_obj, '__validate__', None)
            if func is not None:
                func(value)

        # Only way to set class attributes
        super().__setattr__(name, value)

    def __getattr__(cls, name):
        # TODO - Do some work. This would be called if __getattribute__ fails.
        raise TypeError("Unknown attribute {} given".format(name))


class Foo(metaclass=FooBase):
    pass



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
