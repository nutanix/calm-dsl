from jsonschema import _utils
from jsonschema import Draft7Validator, validators
from jsonschema.exceptions import _Error
from jsonschema._utils import ensure_list, types_msg, unbool
import textwrap
from ruamel import yaml
import json

_unset = _utils.Unset()


class validation_error(_Error):

    _word_for_schema_in_error_message = "validating schema"
    _word_for_instance_in_error_message = "instance schema"

    def __unicode__(self):
        essential_for_verbose = (
            self.validator,
            self.validator_value,
            self.instance,
            self.schema,
        )
        if any(m is _unset for m in essential_for_verbose):
            return self.message

        self.schema = yaml.dump(
            json.loads(json.dumps(self.schema, sort_keys=True, indent=4))
        )
        self.instance = yaml.dump(
            json.loads(json.dumps(self.instance, sort_keys=True, indent=4))
        )

        pschema = yaml.dump(self.schema, default_flow_style=False)
        pinstance = yaml.dump(self.instance, default_flow_style=False)

        return self.message + textwrap.dedent(
            """

            Failed validating %s at %s:
            %s

            By %r validator in %s at %s:
            %s
            """.rstrip()
        ) % (
            self._word_for_instance_in_error_message,
            _utils.format_as_index(self.relative_path),
            pinstance,
            self.validator,
            self._word_for_schema_in_error_message,
            _utils.format_as_index(list(self.relative_schema_path)[:-1]),
            pschema,
        )

    __str__ = __unicode__


# Note: Override any new property used in provider schema for proper traceback
# Supported properties for now: ["property", "anyOf", "type", "enum", "minLength", "maxLength"]
def extend_validator(ValidatorClass):
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
                    value, properties[property], path=property, schema_path=property
                ):
                    yield error

            else:
                error = "Additional properties are not allowed : %r" % (property)
                yield validation_error(error)

    def anyOf(validator, anyOf, instance, schema):
        all_errors = []
        for index, subschema in enumerate(anyOf):
            errs = list(validator.descend(instance, subschema, schema_path=index))
            if not errs:
                break
            all_errors.extend(errs)
        else:
            yield validation_error(
                "%r is not valid under any of the given schemas" % (instance,),
                context=all_errors,
            )

    def type(validator, types, instance, schema):
        types = ensure_list(types)

        if not any(validator.is_type(instance, type) for type in types):
            yield validation_error(types_msg(instance, types))

    def minLength(validator, mL, instance, schema):
        if validator.is_type(instance, "string") and len(instance) < mL:
            yield validation_error("%r is too short" % (instance,))

    def maxLength(validator, mL, instance, schema):
        if validator.is_type(instance, "string") and len(instance) > mL:
            yield validation_error("%r is too long" % (instance,))

    def enum(validator, enums, instance, schema):
        if instance == 0 or instance == 1:
            unbooled = unbool(instance)
            if all(unbooled != unbool(each) for each in enums):
                yield validation_error("%r is not one of %r" % (instance, enums))
        elif instance not in enums:
            yield validation_error("%r is not one of %r" % (instance, enums))

    return validators.extend(
        ValidatorClass,
        {
            "properties": properties,
            "anyOf": anyOf,
            "type": type,
            "minLength": minLength,
            "maxLength": maxLength,
            "enum": enum,
        },
    )


StrictDraft7Validator = extend_validator(Draft7Validator)
