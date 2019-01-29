import ast
import inspect
import textwrap
import json
import tokenize

import asttokens


class Entity:

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if not isinstance(value, type(self)):
            raise TypeError('{} is not of type {}.'.format(value, type(self)))
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class List:

    def __init__(self, item_type):
        self.item_type = item_type

    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, values):

        if not isinstance(values, list):
            raise TypeError('{} is not of type {}.'.format(values, list))

        for value in values:
            if not isinstance(value, self.item_type):
                raise TypeError('{} is not of type {}.'.format(value, self.item_type))

        instance.__dict__[self.name] = values

    def __set_name__(self, owner, name):
        self.name = name


class Substrate(Entity):
    pass


class Service(Entity):
    pass


class Deployment(Entity):

    substrate = Substrate()
    services = List(Service)

    def __init_subclass__(cls, **kwargs):

        super().__init_subclass__(**kwargs)

        print("Introspecting {} ...".format(cls))
        fns = inspect.getmembers(cls, predicate=inspect.isfunction)
        for fn_name, fn_obj in fns:
            if fn_name == "__init__":
                code = textwrap.dedent(inspect.getsource(fn_obj))
                print(code)
                tree = parse(code)
                jsn = export_json(tree, pretty_print=True)
                print(jsn)


class Profile(Entity):

    deployments = List(Deployment)


class Blueprint(Entity):

    profiles = List(Profile)




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
