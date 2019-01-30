import ast
import inspect
import textwrap
import json
from json import JSONEncoder
import tokenize

import asttokens


class BaseType:

    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class NonNegativeType(BaseType):

    def __set__(self, instance, value):
        if value < 0:
            raise ValueError('Cannot be negative.')
        instance.__dict__[self.name] = value


class EntityType(BaseType):

    def __init__(self, entity_type):
        self.entity_type = entity_type

    def __set__(self, instance, value):
        if not isinstance(value, self.entity_type):
            raise TypeError('{} is not of type {}.'.format(type(value), self.entity_type))
        instance.__dict__[self.name] = value


class EntityListType(EntityType):

    def __set__(self, instance, values):

        if not isinstance(values, list):
            raise TypeError('{} is not of type {}.'.format(type(values), list))

        for value in values:
            if not isinstance(value, self.entity_type):
                raise TypeError('{} is not of type {}.'.format(type(value), self.entity_type))

        instance.__dict__[self.name] = values


class StringType(EntityType):

    def __init__(self):
        super().__init__(str)


class BoolType(EntityType):

    def __init__(self):
        super().__init__(bool)


class DictType(EntityType):

    def __init__(self):
        super().__init__(dict)


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


class EntityJSONEncoder(JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'json_repr'):
            return obj.json_repr()
        else:
            return super().default(obj)


class EntityBase:

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)


class Entity(EntityBase):

    attributes = {}
    _default_attrs = {}

    def __str__(self):
        return str(self._all_attrs)

    def json_repr(self):
        return self._all_attrs

    def json_dumps(self, pprint=False, sort_keys=False):
        return json.dumps(self.json_repr(),
                          cls=EntityJSONEncoder,
                          sort_keys=sort_keys,
                          indent=4 if pprint else None,
                          separators=(",", ": ") if pprint else (",", ":")
        )

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


class PortBase(EntityBase):

    def __init_subclass__(cls, **kwargs):

        cls._default_attrs = {
            "target_port": "",
            "protocol": "",
            "endpoint_name": "",
            "exposed_address": "",
            "exposed_port": "",
            "container_spec": dict(),
        }

        super().__init_subclass__(**kwargs)


class Port(Entity, PortBase):

    target_port = StringType()
    protocol = StringType()
    endpoint_name = StringType()
    exposed_address = StringType()
    exposed_port = StringType()
    container_spec = DictType()


class ServiceBase(EntityBase):

    def __init_subclass__(cls, **kwargs):

        cls._default_attrs = {
            "name": cls.__name__,
            "description": cls.__doc__,
            "port_list": [],
            "singleton": False,
            "tier": "",

        }

        super().__init_subclass__(**kwargs)


class Service(Entity, ServiceBase):

    port_list = PortListType()
    singleton = BoolType()
    tier = StringType()


class SubstrateBase(EntityBase):

    def __init_subclass__(cls, **kwargs):

        cls._default_attrs = {}

        super().__init_subclass__(**kwargs)


class Substrate(Entity, SubstrateBase):
    pass


class DeploymentBase(EntityBase):

    def __init_subclass__(cls, **kwargs):

        cls._default_attrs = {
            "substrate": None,
            "services": [],
            "min_replicas": 1,
            "max_replicas": 1,
        }

        super().__init_subclass__(**kwargs)


class Deployment(Entity, DeploymentBase):

    substrate = SubstrateType()
    services = ServiceListType()
    min_replicas = NonNegativeType()
    max_replicas = NonNegativeType()


class ProfileBase(EntityBase):

    def __init_subclass__(cls, **kwargs):

        cls._default_attrs = {
            "deployments": [],
        }


class Profile(Entity, ProfileBase):

    deployments = DeploymentListType()


class BlueprintBase(EntityBase):

    def __init_subclass__(cls, **kwargs):

        cls._default_attrs = {
            "profiles": [],
        }


class Blueprint(Entity, BlueprintBase):

    profiles = ProfileListType()


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
