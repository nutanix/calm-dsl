
from ruamel import yaml
from jinja2 import Environment, PackageLoader
from io import StringIO
import jsonref, json
from calm.dsl.providers.validator_helper import ValidatorType, TypeChecker

class AHV_Validator(object):

    def __init__(self):

        loader = PackageLoader("calm.dsl.providers", "ahv")
        env = Environment(loader=loader)
        template = env.get_template("ahv_create_spec.yaml.jinja2")
        tdict = yaml.safe_load(StringIO(template.render()))
        tdict = jsonref.loads(json.dumps(tdict))

        self.schema = tdict["components"]["schemas"]["create_spec"]
        self.checker = TypeChecker()

    
    def is_type(self, spec_instance, type):

        return self.checker.is_type(spec_instance, type)

    
    def iter_errors(self, spec_instance, schema=None):

        if schema is None:
            schema = self.schema

        for key, value in schema.items():
            validator = ValidatorType.validators.get(key)
            if validator is None:
                raise Exception(
                    'undefined property: {} mentioned in the schema'. format(key)
                )

            validator(self, value, spec_instance)

    
    def validate(self, spec):

        self.iter_errors(spec_instance = spec)
