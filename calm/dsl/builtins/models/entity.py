from collections import OrderedDict
import json
from json import JSONEncoder, JSONDecoder
import sys

from ruamel.yaml import YAML

from .schema import get_schema_details


class EntityDict(OrderedDict):

    def __init__(self, validators):
        self.validators = validators

    def _check_name(self, name):
        if name not in self.validators:
            raise TypeError("Unknown attribute {} given".format(name))

    def _validate(self, name, value):

        if not (name.startswith('__') and name.endswith('__')):
            try:
                self._check_name(name)
                ValidatorType, is_array = self.validators[name]
            except:
                # entity should have the capability to define variables
                name = "variables"
                self._check_name(name)
                # get validator for variables
                ValidatorType, _ = self.validators[name]
                print(ValidatorType)
                is_array = False

            if ValidatorType is not None:
                ValidatorType.validate(value, is_array)

    def __setitem__(self, name, value):

        self._validate(name, value)
        super().__setitem__(name, value)


class EntityTypeBase(type):

    subclasses = {}

    @classmethod
    def get_entity_types(cls):
        return cls.subclasses

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not hasattr(cls, "__schema_name__"):
            raise TypeError("Entity type does not have a schema name")

        schema_name = getattr(cls, "__schema_name__")
        cls.subclasses[schema_name] = cls


class EntityType(EntityTypeBase):

    __schema_name__ = None

    @classmethod
    def to_yaml(mcls, representer, node):
        yaml_tag = '!' + mcls.__schema_name__ if mcls.__schema_name__ else "!Entity"
        return representer.represent_mapping(yaml_tag, node.compile())

    @classmethod
    def __prepare__(mcls, name, bases, **kwargs):

        schema_name = mcls.__schema_name__

        # Handle base case (Entity)
        if not schema_name:
            return dict()

        # Check if validators were already set during previous class creation.
        # If yes, then do not set validators again; just return entity dict.

        if not hasattr(mcls, '__validator_dict__'):

            schema_props, validators, defaults, display_map = get_schema_details(schema_name)

            # Set validator dict on metaclass for each prop.
            # To be used during __setattr__() to validate props.
            # Look at validate() for details.
            setattr(mcls, "__validator_dict__", validators)

            # Set defaults which will be used during serialization.
            # Look at json_dumps() for details
            setattr(mcls, "__default_attrs__", defaults)

            # Attach schema properties to metaclass
            setattr(mcls, "__schema_props__", schema_props)

            # Attach display map for compile/decompile
            setattr(mcls, "__display_map__", display_map)


        else:
            validators = getattr(mcls, '__validator_dict__')

        # Class creation would happen using EntityDict() instead of dict().
        # This is done to add validations to class attrs during class creation.
        # Look at __setitem__ in EntityDict
        return EntityDict(validators)

    def __new__(mcls, name, bases, entitydict):

        cls = super().__new__(mcls, name, bases, entitydict)

        setattr(cls, "__kind__", mcls.__schema_name__)

        for k, v in cls.get_all_attrs().items():
            setattr(cls, k, v)

        return cls

    def lookup_validator_type(cls, name):
        # Use metaclass dictionary to get the right validator type
        return type(cls).__validator_dict__.get(name, None)

    def check_name(cls, name):
        if name not in type(cls).__validator_dict__:
            raise TypeError("Unknown attribute {} given".format(name))

    def validate(cls, name, value):

        if not (name.startswith('__') and name.endswith('__')):
            # TODO - refactor with dict validate
            try:
                cls.check_name(name)
                ValidatorType, is_array = cls.lookup_validator_type(name)
            except:
                # entity should have the capability to define variables
                name = "variables"
                cls.check_name(name)
                ValidatorType, _ = cls.lookup_validator_type(name)
                is_array = False

            ValidatorType.validate(value, is_array)

    def __setattr__(cls, name, value):

        # Validate attribute
        cls.validate(name, value)

        # Set attribute
        super().__setattr__(name, value)

    def __str__(cls):
        return cls.__name__

    def __repr__(cls):
        return cls.__name__

    def get_user_attrs(cls):
        user_attrs = {}
        for name, value in cls.__dict__.items():
            if not (name.startswith('__') and name.endswith('__')):
                user_attrs[name] = value

        return user_attrs

    def get_default_attrs(cls):
        default_attrs = {}
        if hasattr(type(cls), '__default_attrs__'):
            default_attrs = getattr(type(cls), '__default_attrs__')

        return default_attrs

    @classmethod
    def check_variables(mcls, user_attrs):

        if not hasattr(mcls, "__validator_dict__"):
            return user_attrs

        if "variables" not in getattr(mcls, "__validator_dict__"):
            return user_attrs

        mod_attrs = {}
        mod_attrs["variables"] = []
        for k, v in user_attrs.items():
            if k not in mcls.__validator_dict__:
                # TODO - make use of k
                mod_attrs["variables"].append(v)
            else:
                mod_attrs[k] = v

        return mod_attrs

    def get_all_attrs(cls):
        default_attrs = cls.get_default_attrs()
        user_attrs = cls.get_user_attrs()

        mod_attrs = cls.check_variables(user_attrs)

        # Merge both attrs. Overwrite user attrs on default attrs
        return {**default_attrs, **mod_attrs}

    def compile(cls):

        attrs = cls.get_all_attrs()

        # convert keys to api schema
        cdict = {}
        display_map = getattr(type(cls), "__display_map__")
        for k, v in attrs.items():
            cdict.setdefault(display_map[k], v)

        # Add extra info
        cdict["__name__"] = cls.__name__
        cdict["__doc__"] = cls.__doc__ if cls.__doc__ else ''
        cdict['__kind__'] = cls.__kind__

        return cdict

    @classmethod
    def decompile(mcls, cdict):

        # Remove extra info
        name = cdict.pop("__name__")
        description = cdict.pop("__doc__", None)
        kind = cdict.pop('__kind__')

        # Convert attribute names to x-calm-dsl-display-name, if given
        attrs = {}
        display_map = getattr(mcls, "__display_map__")
        for k, v in cdict.items():
            attrs.setdefault(display_map.inverse[k], v)

        # Create new class based on type
        cls = mcls(name, (Entity, ), attrs)
        cls.__doc__ = description

        return cls

    def json_dumps(cls, pprint=False, sort_keys=False):

        dump = json.dumps(cls,
                          cls=EntityJSONEncoder,
                          sort_keys=sort_keys,
                          indent=4 if pprint else None,
                          separators=(",", ": ") if pprint else (",", ":"))

        # Add newline for pretty print
        return dump + "\n" if pprint else dump

    def json_loads(cls, data):
        return json.loads(data, cls=EntityJSONDecoder)

    def yaml_dump(cls, stream=sys.stdout):

        yaml = YAML()
        types = EntityTypeBase.get_entity_types()

        for _, t in types.items():
            yaml.register_class(t)

        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.dump(cls, stream=stream)


class Entity(metaclass=EntityType):
    pass


class EntityJSONEncoder(JSONEncoder):
    def default(self, cls):

        if not hasattr(cls, '__kind__'):
            return super().default(cls)

        return cls.compile()


class EntityJSONDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, attrs):

        if "__kind__" not in attrs:
            return attrs

        kind = attrs["__kind__"]
        types = EntityTypeBase.get_entity_types()

        Type = types.get(kind, None)
        if not Type:
            raise TypeError("Unknown entity type {} given".format(kind))

        return Type.decompile(attrs)
