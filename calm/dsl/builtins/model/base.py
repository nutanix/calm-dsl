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

from .validator import get_property_validators, BoolValidator


class EntityJSONEncoder(JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'json_repr'):
            return obj.json_repr()
        else:
            return super().default(obj)


template = Environment(
    loader=PackageLoader(
        'calm.dsl',
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
        'calm.dsl',
        'v3schemas')).get_template('main.yaml.jinja2')

v3tdict = yaml.safe_load(StringIO(v3template.render()))
v3tdict = jsonref.loads(json.dumps(v3tdict))
V3SCHEMAS = v3tdict["components"]["schemas"]




###



###

class EntityDict(OrderedDict):

    def __init__(self, schema):
        self.schema = schema.get("properties", {})
        self.property_validators = get_property_validators()

    def get_default_attrs(self):
        defaults = {}
        for name, props in self.schema.items():
            ValidatorType = self.get_validator_type(name)
            defaults[name] = props.get("default", ValidatorType.get_default())

        return defaults

    def get_validator_type(self, name):
        props = self.schema.get(name)
        type_ = props.get("type", None)
        if type_ is None:
            raise Exception("Invalid schema {} given".format(props))

        if type_ == "object" or type_ == "array":
            type_ = props.get("x-calm-dsl-type", None)
            if type_ is None:
                raise Exception("x-calm-dsl-type extension for {} not found".format(name))

        ValidatorType = self.property_validators.get(type_, None)
        if ValidatorType is None:
            raise TypeError("Type {} not supported".format(type_))

        return ValidatorType

    def _check_name(self, name):
        if name not in self.schema:
            raise TypeError("Unknown attribute {} given".format(name))

    def _validate(self, name, value):

        if not (name.startswith('__') and name.endswith('__')):
            self._check_name(name)
            ValidatorType = self.get_validator_type(name)
            ValidatorType.validate(value)

    def __setitem__(self, name, value):

        self._validate(name, value)
        super().__setitem__(name, value)


class EntityType(type):

    __schema__ = {}

    @classmethod
    def __prepare__(mcls, name, bases, **kwargs):
        return EntityDict(schema=mcls.__schema__)

    def __new__(mcls, name, bases, entitydict):

        # Create class
        cls = super().__new__(mcls, name, bases, dict(entitydict))

        # Attach schema to class
        cls.__schema__ = entitydict.schema

        # Set validator type on metaclass for each property name
        # It will be used during __setattr__ to validate props.
        for name in cls.__schema__:
            ValidatorType = entitydict.get_validator_type(name)
            setattr(mcls, name, ValidatorType)

        # Set default attributes
        cls.__default_attrs__ = entitydict.get_default_attrs()

        return cls

    def __init__(cls, name, bases, classdict):

        cls.__default_attrs__["name"] = cls.__name__
        cls.__default_attrs__["description"] = '' if cls.__doc__ is None else cls.__doc__

    def get_validator_type(cls, name):
        return type(cls).__dict__.get(name, None)

    def check_name(cls, name):
        if name not in cls.__schema__:
            raise TypeError("Unknown attribute {} given".format(name))

    def _validate(cls, name, value):

        if not (name.startswith('__') and name.endswith('__')):
            cls.check_name(name)
            ValidatorType = cls.get_validator_type(name)
            ValidatorType.validate(value)

    def __setattr__(cls, name, value):

        # Validate attribute
        cls._validate(name, value)

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


class Entity(metaclass=EntityType):
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

        setattr(type(cls), "singleton", BoolValidator())

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
