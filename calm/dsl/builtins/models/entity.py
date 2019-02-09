from collections import OrderedDict
import json
from json import JSONEncoder

from .schema import get_schema_props, get_validator_details


class EntityDict(OrderedDict):

    def __init__(self, schema_props):
        self.schema_props = schema_props

    def _check_name(self, name):
        if name not in self.schema_props:
            raise TypeError("Unknown attribute {} given".format(name))

    def _validate(self, name, value):

        if not (name.startswith('__') and name.endswith('__')):
            self._check_name(name)
            ValidatorType, is_array, _ = get_validator_details(self.schema_props, name)
            ValidatorType.validate(value, is_array)

    def __setitem__(self, name, value):

        self._validate(name, value)
        super().__setitem__(name, value)


class EntityType(type):

    __schema_name__ = None

    @classmethod
    def __prepare__(mcls, name, bases, **kwargs):

        schema_name = mcls.__schema_name__

        # Handle base case (Entity)
        if not schema_name:
            return dict()

        schema_props = get_schema_props(schema_name)

        default_attrs = {}
        for name, props in schema_props.items():
            # Set validator type on metaclass for each property name
            # To be used explicitly during __setattr__() to validate props.
            # Look at validate() for details.
            ValidatorType, is_array, default = get_validator_details(schema_props, name)
            if ValidatorType is not None:
                setattr(mcls, name, (ValidatorType, is_array))
                # Set default attribute
                default_attrs[name] = default

        # Attach schema properties and defaults to metaclass
        setattr(mcls, "__schema_props__", schema_props)
        setattr(mcls, "__default_attrs__", default_attrs)

        # Class creation would happen using EntityDict() instead of dict().
        # This is done to add validations to class attrs during class creation.
        return EntityDict(schema_props)

    def lookup_validator_type(cls, name):
        # Use metaclass dictionary to get the right validator type
        return type(cls).__dict__.get(name, None)

    def check_name(cls, name):
        if name not in type(cls).__schema_props__:
            raise TypeError("Unknown attribute {} given".format(name))

    def validate(cls, name, value):

        if not (name.startswith('__') and name.endswith('__')):
            cls.check_name(name)
            ValidatorType, is_array = cls.lookup_validator_type(name)
            ValidatorType.validate(value, is_array)

    def __setattr__(cls, name, value):

        # Validate attribute
        cls.validate(name, value)

        # Set attribute
        super().__setattr__(name, value)

    def __str__(cls):
        return cls.__name__

    def get_user_attrs(cls):
        user_attrs = {}
        user_attrs["name"] = cls.__name__
        user_attrs["description"] = cls.__doc__ if cls.__doc__ else ''
        for name, value in cls.__dict__.items():
            if not (name.startswith('__') and name.endswith('__')):
                user_attrs[name] = value

        return user_attrs

    def get_default_attrs(cls):
        return type(cls).__default_attrs__

    def json_repr(cls):

        default_attrs = cls.get_default_attrs()
        user_attrs = cls.get_user_attrs()

        # Merge both attrs. Overwrite user attrs on default attrs
        return {**default_attrs, **user_attrs}

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
