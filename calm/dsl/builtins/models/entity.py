from collections import OrderedDict
import json
from json import JSONEncoder, JSONDecoder
import sys
from types import MappingProxyType
import uuid

from ruamel.yaml import YAML, resolver, SafeRepresenter
from calm.dsl.tools import StrictDraft7Validator
from calm.dsl.tools import get_logging_handle
from .schema import get_schema_details

LOG = get_logging_handle(__name__)


def _validate(vdict, name, value):

    if name.startswith("__") and name.endswith("__"):
        return value

    try:

        if name not in vdict:
            raise TypeError("Unknown attribute {} given".format(name))
        ValidatorType, is_array = vdict[name]
        if getattr(ValidatorType, "__is_object__", False):
            return ValidatorType.validate(value, is_array)

    except TypeError:

        # Check if value is a variable/action
        types = EntityTypeBase.get_entity_types()
        VariableType = types.get("Variable", None)
        if not VariableType:
            raise TypeError("Variable type not defined")
        DescriptorType = types.get("Descriptor", None)
        if not DescriptorType:
            raise TypeError("Descriptor type not defined")
        if not (
            ("variables" in vdict and isinstance(value, (VariableType,)))
            or ("actions" in vdict and isinstance(type(value), DescriptorType))
        ):
            LOG.debug("Validating object: {}".format(vdict))
            raise

        # Validate and set variable/action
        # get validator for variables/action
        if isinstance(value, VariableType):
            ValidatorType, _ = vdict["variables"]
            # Set name attribute in variable
            setattr(value, "name", name)

        elif isinstance(type(value), DescriptorType):
            ValidatorType = None
        is_array = False

    if ValidatorType is not None:
        ValidatorType.validate(value, is_array)
    return value


class EntityDict(OrderedDict):
    def __init__(self, validators):
        self.validators = validators

    def _validate(self, name, value):
        vdict = self.validators
        return _validate(vdict, name, value)

    def __setitem__(self, name, value):
        value = self._validate(name, value)
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

        # Handle base case (Entity)
        if not schema_name:
            return

        # Set properties on metaclass by fetching from schema
        (schema_props, validators, defaults, display_map) = get_schema_details(
            schema_name
        )

        # Set validator dict on metaclass for each prop.
        # To be used during __setattr__() to validate props.
        # Look at validate() for details.
        setattr(cls, "__validator_dict__", MappingProxyType(validators))

        # Set defaults which will be used during serialization.
        # Look at json_dumps() for details
        setattr(cls, "__default_attrs__", MappingProxyType(defaults))

        # Attach schema properties to metaclass
        setattr(cls, "__schema_props__", MappingProxyType(schema_props))

        # Attach display map for compile/decompile
        setattr(cls, "__display_map__", MappingProxyType(display_map))


class EntityType(EntityTypeBase):

    __schema_name__ = None
    __openapi_type__ = None

    def validate_dict(cls, entity_dict):
        schema = {"type": "object", "properties": cls.__schema_props__}
        validator = StrictDraft7Validator(schema)
        validator.validate(entity_dict)

    @classmethod
    def to_yaml(mcls, representer, node):
        yaml_tag = resolver.BaseResolver.DEFAULT_MAPPING_TAG
        return representer.represent_mapping(yaml_tag, node.compile())

    @classmethod
    def __prepare__(mcls, name, bases):

        schema_name = mcls.__schema_name__

        # Handle base case (Entity)
        if not schema_name:
            return dict()

        validators = getattr(mcls, "__validator_dict__")

        # Class creation would happen using EntityDict() instead of dict().
        # This is done to add validations to class attrs during class creation.
        # Look at __setitem__ in EntityDict
        return EntityDict(validators)

    def __new__(mcls, name, bases, kwargs):

        if not isinstance(kwargs, EntityDict):
            entitydict = mcls.__prepare__(name, bases)
            for k, v in kwargs.items():
                entitydict[k] = v
        else:
            entitydict = kwargs

        schema_name = getattr(mcls, "__schema_name__")

        if not name:
            # Generate unique name
            name = "_" + schema_name + str(uuid.uuid4())[:8]
        else:
            if name == schema_name:
                raise TypeError("{} is a reserved name for this entity".format(name))

        cls = super().__new__(mcls, name, bases, entitydict)

        openapi_type = getattr(mcls, "__openapi_type__")
        setattr(cls, "__kind__", openapi_type)

        for k, v in cls.get_default_attrs().items():
            # Check if attr was set during class creation
            # else - set default value
            if not hasattr(cls, k):
                setattr(cls, k, v)

        return cls

    @classmethod
    def validate(mcls, name, value):
        if hasattr(mcls, "__validator_dict__"):
            vdict = mcls.__validator_dict__
            return _validate(vdict, name, value)

    def __setattr__(cls, name, value):

        # Validate attribute
        value = cls.validate(name, value)

        # Set attribute
        super().__setattr__(name, value)

    def __str__(cls):
        return cls.__name__

    def __repr__(cls):
        return cls.__name__

    def get_user_attrs(cls):
        types = EntityTypeBase.get_entity_types()
        ActionType = types.get("Action", None)
        VariableType = types.get("Variable", None)
        DescriptorType = types.get("Descriptor", None)
        user_attrs = {}
        for name, value in cls.__dict__.items():
            if (
                name.startswith("__")
                and name.endswith("__")
                and not isinstance(value, (VariableType, ActionType))
                and not isinstance(type(value), DescriptorType)
            ):
                continue
            user_attrs[name] = getattr(cls, name, value)

        return user_attrs

    @classmethod
    def get_default_attrs(mcls):
        ret = {}
        default_attrs = getattr(mcls, "__default_attrs__", {}) or {}

        for key, value in default_attrs.items():
            ret[key] = value()

        # return a deepcopy, this dict or it's contents should NEVER be modified
        return ret

    @classmethod
    def update_attrs(mcls, attrs):

        if not hasattr(mcls, "__validator_dict__"):
            return

        vdict = getattr(mcls, "__validator_dict__")
        if "variables" not in vdict and "actions" not in vdict:
            return

        # Variables and actions have [] as defaults.
        # As this list can be modified/extended here,
        # make a copy of variables and actions
        attrs["variables"] = list(attrs.get("variables", []))
        if "actions" in vdict:
            attrs["actions"] = list(attrs.get("actions", []))

        types = EntityTypeBase.get_entity_types()
        ActionType = types.get("Action", None)
        VariableType = types.get("Variable", None)
        DescriptorType = types.get("Descriptor", None)

        # Update list of variables with given class-level variables
        del_keys = []
        for key, value in attrs.items():
            if key not in vdict:
                if isinstance(value, ActionType):
                    attr_name = "actions"
                elif isinstance(value, VariableType):
                    attr_name = "variables"
                elif isinstance(value.__class__, DescriptorType):
                    exception = getattr(value, "__exception__", None)
                    if exception:
                        raise exception
                else:
                    raise TypeError(
                        "Field {} has value of type {} ".format(key, type(value))
                        + "but it is not handled for this entity"
                    )
                attrs[attr_name].append(value)
                del_keys.append(key)

        # Delete attrs
        for k in del_keys:
            attrs.pop(k)

    def get_all_attrs(cls):

        ncls_ns = cls.get_default_attrs()
        for klass in reversed(cls.mro()):
            if hasattr(klass, "get_user_attrs") and callable(
                getattr(klass, "get_user_attrs")
            ):
                ncls_ns = {**ncls_ns, **klass.__dict__}

        ncls = type(cls)(cls.__name__, cls.__bases__, ncls_ns)

        return ncls.get_user_attrs()

    def compile(cls):

        attrs = cls.get_all_attrs()
        cls.update_attrs(attrs)

        # convert keys to api schema
        cdict = {}
        display_map = getattr(type(cls), "__display_map__")
        for k, v in attrs.items():
            if getattr(v, "__is_object__", False):
                cdict.setdefault(display_map[k], v.compile(cls))
            cdict.setdefault(display_map[k], v)

        # Add name & description if present
        if "name" in cdict and cdict["name"] == "":
            cdict["name"] = cls.__name__

        if "description" in cdict and cdict["description"] == "":
            cdict["description"] = cls.__doc__ if cls.__doc__ else ""

        # Add extra info for roundtrip
        # TODO - remove during serialization before sending to server
        # cdict['__kind__'] = cls.__kind__

        return cdict

    @classmethod
    def decompile(mcls, cdict):

        # Remove extra info
        name = cdict.pop("name", mcls.__schema_name__)
        description = cdict.pop("description", None)
        # kind = cdict.pop('__kind__')

        # Convert attribute names to x-calm-dsl-display-name, if given
        attrs = {}
        display_map = getattr(mcls, "__display_map__")
        for k, v in cdict.items():
            attrs.setdefault(display_map.inverse[k], v)

        # Create new class based on type
        cls = mcls(name, (Entity,), attrs)
        cls.__doc__ = description

        return cls

    def json_dumps(cls, pprint=False, sort_keys=False):

        dump = json.dumps(
            cls,
            cls=EntityJSONEncoder,
            sort_keys=sort_keys,
            indent=4 if pprint else None,
            separators=(",", ": ") if pprint else (",", ":"),
        )

        # Add newline for pretty print
        return dump + "\n" if pprint else dump

    def json_loads(cls, data):
        return json.loads(data, cls=EntityJSONDecoder)

    def yaml_dump(cls, stream=sys.stdout):
        class MyRepresenter(SafeRepresenter):
            def ignore_aliases(self, data):
                return True

        yaml = YAML(typ="safe")
        yaml.default_flow_style = False
        yaml.Representer = MyRepresenter

        types = EntityTypeBase.get_entity_types()

        for _, t in types.items():
            yaml.register_class(t)

        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.dump(cls, stream=stream)

    def get_ref(cls, kind=None):
        types = EntityTypeBase.get_entity_types()
        ref = types.get("Ref")
        if not ref:
            return
        name = None
        bases = (Entity,)
        if ref:
            attrs = {}
            attrs["name"] = str(cls)
            attrs["kind"] = kind or getattr(cls, "__kind__")
        return ref(name, bases, attrs)

    def get_dict(cls):
        return json.loads(cls.json_dumps())


class Entity(metaclass=EntityType):
    pass


class EntityJSONEncoder(JSONEncoder):
    def default(self, cls):

        if not hasattr(cls, "__kind__"):
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
