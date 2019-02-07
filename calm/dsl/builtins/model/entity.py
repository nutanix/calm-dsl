from collections import OrderedDict
import json
from json import JSONEncoder

from .validator import get_property_validators


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


class EntityJSONEncoder(JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'json_repr'):
            return obj.json_repr()
        else:
            return super().default(obj)
