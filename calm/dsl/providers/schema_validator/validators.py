from jsonschema import Draft7Validator, validators, exceptions


def set_additional_properties_false(validator_cls):
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

    return validators.extend(validator_cls, {"properties": properties})


validator = set_additional_properties_false(Draft7Validator)
