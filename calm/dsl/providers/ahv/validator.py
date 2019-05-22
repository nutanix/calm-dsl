from ruamel import yaml
from jinja2 import Environment, PackageLoader
from io import StringIO
import jsonref, json
from ..schema_validator import validator
from ..providers import Validator_Base


class AHV_Validator(Validator_Base, vm_type="AHV_VM"):
    def __init__(self):

        loader = PackageLoader(__name__, ".")
        env = Environment(loader=loader)
        template = env.get_template("ahv_create_spec.yaml.jinja2")
        tdict = yaml.safe_load(StringIO(template.render()))
        tdict = jsonref.loads(json.dumps(tdict))

        self.schema = tdict["components"]["schemas"]["create_spec"]
        self.validator = validator(self.schema)

    def validate(self, spec):

        self.validator.validate(spec)
