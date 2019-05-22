from io import StringIO
from pathlib import Path, PurePath
import json

from ruamel import yaml
from jinja2 import Environment, PackageLoader
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


class ProviderType(type):

    providers = {}

    def __new__(mcls, name, bases, ns):

        cls = super().__new__(mcls, name, bases, ns)

        provider_type = ns.get("provider_type")
        if provider_type is None:
            raise Exception("Provider type not given.")

        cls.provider_type = provider_type

        provider_spec = ns.get("provider_spec")
        if provider_spec is None:
            raise Exception("Provider spec not given.")

        cls.provider_spec = provider_spec

        cls.validator = StrictDraft7Validator(provider_spec)

        cls.providers[provider_type] = cls

        return cls

    def validate(cls, spec):
        cls.validator.validate(spec)


def get_provider(provider_type):

    if provider_type not in ProviderType.providers:
        raise Exception("provider not registered")

    return ProviderType.providers[provider_type]


def get_providers():
    return ProviderType.providers


def read_schema(spec_template_file):

    loader = PackageLoader(__name__, "schemas")
    env = Environment(loader=loader)
    template = env.get_template(spec_template_file)
    tdict = yaml.safe_load(StringIO(template.render()))
    tdict = jsonref.loads(json.dumps(tdict))

    # TODO - Check if keys are present
    provider_type = tdict["info"]["title"]
    provider_spec = tdict["components"]["schemas"]["provider_spec"]
    return provider_type, provider_spec


def register_providers():

    path = Path(__file__)

    for filename in list(path.parent.glob("schemas/*.yaml.jinja2")):

        # Get spec template
        spec_template_file = PurePath(filename).name

        # Read spec schema
        provider_type, provider_spec = read_schema(spec_template_file)

        # Create namespace dict for class
        ns = {
            "provider_type": provider_type,
            "provider_spec": provider_spec,
        }

        # Create provider class

        # removes .yaml and .jinja2 suffix
        file_stem = PurePath(PurePath(filename).stem).stem
        name = file_stem.title().replace("_", "")

        bases = (object, )
        ProviderType(name, bases, ns)


def main():
    register_providers()


if __name__ == "__main__":
    main()
