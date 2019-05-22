from ruamel import yaml
from jinja2 import Environment, PackageLoader
from io import StringIO
import json
import jsonref
from jsonschema import Draft7Validator, validators, exceptions


def set_additional_properties_false(ValidatorClass):
    def properties(validator, properties, instance, schema):
        if not validator.is_type(instance, "object"):
            return

        # for managing defaults in the schema
        for property, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])

        # for handling additional properties found in user spec
        for property, value in instance.items():

            if property in properties:
                for error in validator.descend(
                    value,
                    properties[property],
                    path=properties[property],
                    schema_path=properties[property],
                ):
                    yield error

            else:
                error = "Additional properties are not allowed : %r" % (property)
                yield exceptions.ValidationError(error)

    return validators.extend(ValidatorClass, {"properties": properties})


StrictDraft7Validator = set_additional_properties_false(Draft7Validator)


class ProviderInterface:

    providers = {}

    @staticmethod
    def _get_schema(package_name, spec_template):

        if package_name is None:
            raise Exception("Package name not given.")

        loader = PackageLoader(package_name, ".")
        env = Environment(loader=loader)
        template = env.get_template(spec_template)
        tdict = yaml.safe_load(StringIO(template.render()))
        tdict = jsonref.loads(json.dumps(tdict))

        # TODO - Check if keys are present
        schema = tdict["components"]["schemas"]["provider_spec"]
        return schema

    def __init_subclass__(
        cls,
        provider_type,
        package_name,
        spec_template="provider_spec.yaml.jinja2",
        **kwargs
    ):
        super().__init_subclass__(**kwargs)

        if provider_type is None:
            raise Exception("Provider Type not given.")

        schema = cls._get_schema(package_name, spec_template)
        cls.validator = StrictDraft7Validator(schema)

        cls.providers[provider_type] = cls

    @classmethod
    def validate(cls, spec):
        cls.validator.validate(spec)


def get_provider_interface():
    return ProviderInterface


def get_provider(provider_type):

    if provider_type not in ProviderInterface.providers:
        raise Exception("provider not registered")

    return ProviderInterface.providers[provider_type]
