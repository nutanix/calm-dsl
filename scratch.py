import ast
import inspect


class Service:

    def dump(self, dct):
        dump("service", self, dct)


class Substrate:

    def dump(self, dct):
        dump("substrate", self, dct)


class SubstrateType:

    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if not isinstance(value, Substrate):
            raise TypeError('Got {} type. Looking for {}.'.format(
                type(value), Substrate))
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class MetaDeployment(type):

    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)

        # TODO - Use inspect to allow only legal operations
        print(inspect.getmembers(x, predicate=inspect.isfunction))
        return x


class Deployment(metaclass=MetaDeployment):
    substrate = SubstrateType()

    def add_substrate(self, substrate):
        self.substrate = substrate

    def add_services(self, services):
        self.services = services

    def dump(self, dct):

        dump("deployment", self, dct)

        self.substrate.dump(dct)

        for service in self.services:
            service.dump(dct)

        return dct


class Profile:

    def add_deployments(self, deployments):
        self.deployments = deployments


    def dump(self, dct):

        dump("profile", self, dct)

        for deployment in self.deployments:
            deployment.dump(dct)

        return dct



class Blueprint:

    def add_profiles(self, profiles):
        self.profiles = profiles

    def get_default_profile(self):
        return self.profiles[0]

    def dump(self, dct):

        dump("blueprint", self, dct)

        profile = self.get_default_profile()
        profile.dump(dct)

        return dct



###


def dump(name, obj, dct):
    code = inspect.getsource(type(obj))
    tree = ast.parse(code)
    dct[name] = export_dict(tree)


def export_dict(tree):
    assert(isinstance(tree, ast.AST))
    return DictExportVisitor().visit(tree)


class DictExportVisitor:
    ast_type_field = "ast_type"

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
        return args

    def default_visit_field(self, val):
        if isinstance(val, ast.AST):
            return self.visit(val)
        elif isinstance(val, list) or isinstance(val, tuple):
            return [self.visit(x) for x in val]
        else:
            return val

    def visit_str(self, val):
        return str(val)

    def visit_Bytes(self, val):
        return str(val.s)

    def visit_NoneType(self, val):
        return None

    def visit_field_NameConstant_value(self, val):
        return str(val)

    def visit_field_Num_n(self, val):
        if isinstance(val, int):
            return {
                self.ast_type_field: "int",
                "n": val,
                # JavaScript integers are limited to 2**53 - 1 bits,
                # so we add a string representation of the integer
                "n_str": str(val),
            }
        elif isinstance(val, float):
            return {
                self.ast_type_field: "float",
                "n": val
            }
        elif isinstance(val, complex):
            return {
                self.ast_type_field: "complex",
                "n": val.real,
                "i": val.imag
            }
