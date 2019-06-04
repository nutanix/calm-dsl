from ruamel import yaml
from jinja2 import Environment, PackageLoader
from jsonschema import Draft7Validator, validators, exceptions
from io import StringIO

import jsonref
import json


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


def get_validator():
    template_file = "project.yaml.jinja2"

    loader = PackageLoader(__name__, "schemas")
    env = Environment(loader=loader)
    template = env.get_template(template_file)
    tdict = yaml.safe_load(StringIO(template.render()))
    tdict = jsonref.loads(json.dumps(tdict))

    return StrictDraft7Validator(tdict)


class Validator:

    def __init__(self):
        self.validator = get_validator()

    def validate(self, spec):
        self.validator.validate(spec)
