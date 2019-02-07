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


template = Environment(
    loader=PackageLoader(
        __name__,
        'schemas')).get_template('main.yaml.jinja2')

tdict = yaml.safe_load(StringIO(template.render()))

# Check if all references are resolved
tdict = jsonref.loads(json.dumps(tdict))
# print(json.dumps(tdict, cls=EntityJSONEncoder, indent=4, separators=(",", ": ")))

SCHEMAS = tdict["components"]["schemas"]

# Load v3 schema objects
# TODO - refactor

v3template = Environment(
    loader=PackageLoader(
        __name__,
        'v3schemas')).get_template('main.yaml.jinja2')

v3tdict = yaml.safe_load(StringIO(v3template.render()))
v3tdict = jsonref.loads(json.dumps(v3tdict))
V3SCHEMAS = v3tdict["components"]["schemas"]


class EntityType:

    __default__ = None

    @classmethod
    def get_default(cls):
        return cls.__default__

    def __init__(self, entity_type, **kwargs):
        self.entity_type = entity_type
        self.is_array = True if isinstance(self.get_default(), list) else False

    def get(self, instance, owner):
        return instance.__dict__[self.name]

    def _validate_item(self, value):
        if not isinstance(value, self.entity_type):
            raise TypeError(
                '{} is not of type {}.'.format(
                    value, self.entity_type))

    def _validate_list(self, values):
        if not isinstance(values, list):
            raise TypeError('{} is not of type {}.'.format(values, list))

    def validate(self, value):
        if not self.is_array:
            self._validate_item(value)
        else:
            self._validate_list(value)
            for v in value:
                self._validate_item(v)

    def set_name(self, owner, name):
        self.name = name

    # Too much magic going on with `__set__()` as described below!
    # Owner classes should call `__validate__()` explicitly through descriptors in
    # `type(instance).__setattr()`and use `super().__settar__()` in owner class
    # to set attributes. More details below.

    # def __set__(self, instance, value):
    #     """ The below dict assignmet does not work for type objects like classes as
    #     `cls.__dict__` is immutable and exposed through a `mappingproxy` which
    #     is read-only.

    #     `object.__setattr__(instance, name, value)` will also not work as this specifically
    #     checks if the first argument is a subclass of `object`. `instance` here would
    #     be a `type` object for class and hence this will fail.
    #     The check is there to prevent this method being used to modify built-in
    #     types (Carlo Verre hack).

    #     So, descriptors cannot work in current form on type classes (eg. metaclass) as class
    #     attributes are stored as `mappingproxy` objects. So only
    #     `class.__setattr__` remains as an avenue for setting class attributes.

    #     Now, `setattr` works by looking for a data descriptor in
    #     `type(obj).__mro__`. If a data descriptor is found (i.e. if __set__ is defined),
    #     it calls `__set__` and exits.
    #     There is no way to avoid this, and uderstandably so, as this is the purpose
    #     of the magical `__set__` interface.

    #     But, as `class.__dict__` cannot be used to set attribute,
    #     `setattr(cls, self.name, value)` is the only way.
    #     Calling setattr inside this block will cause infinite recursion!
    #     Else block below has more details.

    #     """

    #     self.validate(value)

    #     # Does not work if instance is a type object.
    #     if not isinstance(instance, type):
    #         instance.__dict__[self.name] = value
    #         # This works fine.
    #     else:
    #         # setattr(instance, self.name, value)
    #         # This would call __set__ again and hence cause infinite recusion.

    #         # type.__setattr__(instance, self.name, value)
    #         # This would call __set__ again and hence cause infinite recusion.

    #         # instance.__dict__[self.name] = value
    #         # Item assignment for mappingproxy object is not allowed.

    #         # object.__setattr__(instance, self.name, value)
    #         # This does not work as `instance` is a type object.

    #         # Sorry, can't do anything!

    #         pass




class StringType(EntityType):

    __default__ = ''

    def __init__(self, **kwargs):
        super().__init__(str, **kwargs)


class StringListType(StringType):

    __default__ = []


class IntType(EntityType):

    __default__ = 0

    def __init__(self, **kwargs):
        super().__init__(int, **kwargs)


class NonNegativeIntType(IntType):

    def validate(self, value):
        super().validate(Value)
        if value < 0:
            raise ValueError('Cannot be negative.')


class BoolType(EntityType):

    __default__ = False

    def __init__(self, **kwargs):
        super().__init__(bool, **kwargs)


class DictType(EntityType):

    __default__ = {}

    def __init__(self, **kwargs):
        super().__init__(dict, **kwargs)


class PortType(EntityType):

    __default__ = None

    def __init__(self, **kwargs):
        super().__init__(PortBase, **kwargs)


class PortListType(PortType):

    __default__ = []


class ServiceType(EntityType):

    __default__ = None

    def __init__(self, **kwargs):
        super().__init__(ServiceBase, **kwargs)


class ServiceListType(ServiceType):

    __default__ = []


class SubstrateType(EntityType):

    __default__ = None

    def __init__(self, **kwargs):
        super().__init__(SubstrateBase, **kwargs)


class SubstrateListType(SubstrateType):

    __default__ = []


class DeploymentType(EntityType):

    __default__ = None

    def __init__(self, **kwargs):
        super().__init__(DeploymentBase, **kwargs)


class DeploymentListType(DeploymentType):

    __default__ = []


class ProfileType(EntityType):

    __default__ = None

    def __init__(self, **kwargs):
        super().__init__(ProfileBase, **kwargs)


class ProfileListType(ProfileType):

    __default__ = []


###



###

class EntityDict(dict):

    def __init__(self, schema):
        self.schema = schema.get("properties", {})
        self.schema_type_to_descriptor_cls = {

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


class EntityBase(type):

    __schema__ = {}

    @classmethod
    def __prepare__(mcls, name, bases, **kwargs):
        return EntityDict(schema=mcls.__schema__)

    def __new__(mcls, name, bases, entitydict):

        cls = super().__new__(mcls, name, bases, dict(entitydict))

        cls.__schema__ = entitydict.schema

        cls.__default_attrs__ = {}

        for attr, attr_props in cls.__schema__.items():

            attr_type = attr_props.get("type", None)

            if attr_type is None:
                raise Exception("Invalid schema {} given".format(attr_props))

            if attr_type == "object" or attr_type == "array":
                attr_type = attr_props.get("x-calm-dsl-type", None)

                if attr_type is None:
                    raise Exception(
                        "calm dsl extension not found. Invalid schema {}" .format(attr_props))

            DescriptorType = entitydict.schema_type_to_descriptor_cls.get(attr_type, None)
            if DescriptorType is None:
                raise TypeError("Unknown type {} given".format(attr_type))

            descr_obj = DescriptorType()
            setattr(mcls, attr, descr_obj)

            cls.__default_attrs__[attr] = attr_props.get(
                "default", descr_obj.get_default())

        cls.__default_attrs__["name"] = cls.__name__
        cls.__default_attrs__[
            "description"] = cls.__doc__ if cls.__doc__ is not None else ''

        # __set_name__() is called right after class creation which in this case happens
        # in the super() call above. [PEP 487]
        # Call __set_name__() again to set the right attribute names
        for k, v in mcls.__dict__.items():
            func = getattr(v, 'set_name', None)
            if func is not None:
                func(cls, k)

        """
        # Check if any spurious class attibutes are given before class creation
        for key in cls.attributes:
            if key not in cls.__default_attrs__.keys():
                raise KeyError("Unknown key {} given".format(key))
        """

        """
        print("Attrs = {}".format(cls.__default_attrs__))
        print("----------")
        print("Init Class dict = {}".format(cls.__dict__))
        print("----------")
        """

        for k, v in cls.__dict__.items():
            cls._validate_attr(k, v)

        return cls

    def _get_descr_obj(cls, name):

        return type(cls).__dict__.get(name, None)

    def _call_descr_validate(cls, name, value):

        descr_obj = cls._get_descr_obj(name)
        if descr_obj is not None:
            func = getattr(descr_obj, 'validate', None)
            if func is not None:
                func(value)

    def _validate_attr(cls, name, value):

        if not (name.startswith('__') and name.endswith('__')):
            if name not in cls.__default_attrs__:
                raise TypeError("Unknown attribute {} given".format(name))

            cls._call_descr_validate(name, value)

    def __setattr__(cls, name, value):

        # validate attribute
        cls._validate_attr(name, value)

        # Set attribute
        super().__setattr__(name, value)

    def __str__(cls):
        return cls.__name__

    def json_repr(cls):
        user_attrs = {}
        for name, value in cls.__dict__.items():
            if not (name.startswith('__') and name.endswith('__')):
                user_attrs[name] = value

        all_attrs = {
            **cls.__default_attrs__,
            **user_attrs,
        }

        return all_attrs

    def json_dumps(cls, pprint=False, sort_keys=False):
        return json.dumps(cls.json_repr(),
                          cls=EntityJSONEncoder,
                          sort_keys=sort_keys,
                          indent=4 if pprint else None,
                          separators=(",", ": ") if pprint else (",", ":"))


class Entity(metaclass=EntityBase):
    pass


class PortBase(EntityBase):
    __schema__ = SCHEMAS["Port"]


class Port(Entity, metaclass=PortBase):
    pass


class ServiceBase(EntityBase):
    __schema__ = SCHEMAS["Service"]


class Service(Entity, metaclass=ServiceBase):
    pass


class SubstrateBase(EntityBase):
    __schema__ = SCHEMAS["Substrate"]


class Substrate(Entity, metaclass=SubstrateBase):
    pass


class DeploymentBase(EntityBase):
    __schema__ = SCHEMAS["Deployment"]


class Deployment(Entity, metaclass=DeploymentBase):
    pass


class ProfileBase(EntityBase):
    __schema__ = SCHEMAS["Profile"]


class Profile(Entity, metaclass=ProfileBase):
    pass


class BlueprintBase(EntityBase):
    __schema__ = SCHEMAS["Blueprint"]


class Blueprint(Entity, metaclass=BlueprintBase):
    pass


###


def read_vm_spec(filename):

    file_path = os.path.join(
        os.path.dirname(
            inspect.getfile(
                sys._getframe(1))),
        filename)

    with open(file_path, "r") as f:
        return yaml.safe_load(f.read())


###


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

        # print(mcls.__dict__)

        for k, v in mcls.__dict__.items():
            func = getattr(v, '__set_name__', None)
            if func is not None:
                func(mcls, k)

        return cls

    def __setattr__(cls, name, value):
        # print("{}->{}".format(name, value))

        if not (name.startswith('__') and name.endswith('__')):

            if name not in cls.__valid_attrs__:
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
