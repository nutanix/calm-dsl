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


class ValidatorBase:

    validators = {}

    def __init_subclass__(cls, provider_type, **kwargs):
        super().__init_subclass__(**kwargs)

        if provider_type is not None:
            cls.validators[provider_type] = cls

    def __init__(self, package, spec_template="provider_spec.yaml.jinja2"):

        if package is None:
            raise NotImplementedError("No package specified.")

        loader = PackageLoader(package, ".")
        env = Environment(loader=loader)
        template = env.get_template(spec_template)
        tdict = yaml.safe_load(StringIO(template.render()))
        tdict = jsonref.loads(json.dumps(tdict))

        # TODO - Check if keys are present
        self.schema = tdict["components"]["schemas"]["provider_spec"]
        self.validator = StrictDraft7Validator(self.schema)

    def validate(self, spec):
        self.validator.validate(spec)


def get_validator_interface():
    return ValidatorBase


def get_validator(vm_type):

    if vm_type not in ValidatorBase.validators:
        raise Exception("provider not registered")

    return ValidatorBase.validators[vm_type]
