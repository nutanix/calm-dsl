
from calm.dsl.builtins.models.schema import _load_all_schemas
from calm.dsl.builtins.models.spec_validator_helper import TypeChecker,\
     ValidatorType


class ValidatorBase(type):

    def __new__(mcls, name, bases, attrs):

        vm_type = attrs.get('validator_type')
        attrs.pop('validator_type', None)

        type_dict = {
            'AHV': 'ahv_create_spec.yaml.jinja2'
        }

        schema = _load_all_schemas(schema_file=type_dict[vm_type])['create_spec']
        attrs['schema'] = schema
        attrs['checker'] = TypeChecker()

        return super().__new__(mcls, name, bases, attrs)


class SpecValidator(object):

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

        self.iter_errors(spec_instance=spec, schema=self.schema)


class AHV_Validator(SpecValidator, metaclass=ValidatorBase):

    validator_type = 'AHV'
