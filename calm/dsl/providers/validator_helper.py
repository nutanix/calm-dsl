

def is_array(checker, spec_instance):

    return isinstance(spec_instance, list)


def is_bool(checker, spec_instance):

    return isinstance(spec_instance, bool)


def is_integer(checker, spec_instance):

    if isinstance(spec_instance, bool):
        return False
    return isinstance(spec_instance, int)


def is_null(checker, spec_instance):

    return spec_instance is None


def is_object(checker, spec_instance):

    return isinstance(spec_instance, dict)


def is_string(checker, spec_instance):

    return isinstance(spec_instance, str)


class TypeChecker(object):

    checker = {
        u'array': is_array,
        u'boolean': is_bool,
        u'integer': is_integer,
        u'object': is_object,
        u'None': is_null,
        u'string': is_string,
    }

    def is_type(self, spec_instance, type):

        try:
            typeFun = self.checker[type]
            return typeFun(self, spec_instance)

        except:
            raise Exception('Undefined type: %r ' % (type))




def items(validator, items, spec_instance):

    if not validator.is_type(spec_instance, 'array'):
        raise Exception('spec is not of array type')

    for index, item in enumerate(spec_instance):
        validator.iter_errors(item, items)


def minLength(validator, length, spec_instance):

    if not validator.is_type(spec_instance, 'string'):
        raise Exception('spec is not of string type')

    if len(spec_instance) < length:
        raise Exception('%r is too short' % (spec_instance,))


def maxLength(validator, length, spec_instance):

    if not validator.is_type(spec_instance, 'string'):
        raise Exception('spec is not of string type')

    if len(spec_instance) > length:
        raise Exception('%r is too long' % (spec_instance,))


def enum(validator, enums, spec_instance):

    if spec_instance not in enums:
        raise Exception('%r is not one of %r' % (spec_instance, enums))


def properties(validator, properties, spec_instance):

    if not validator.is_type(spec_instance, 'object'):
        raise Exception('spec is not of dict/object type')

    for property, value in spec_instance.items():

        if property in properties:
            validator.iter_errors(
                value,
                properties[property]
            )

        else:
            raise Exception('additional field detected: %r' % (property))


def required(validator, required, spec_instance):

    if not validator.is_type(spec_instance, 'object'):
        raise Exception('spec is not of dict/object type')

    for property in required:
        if property not in spec_instance:
            raise Exception('%r is a required property' % (property))


def allOf(validator, allOf, spec_instance):

    for index, subschema in enumerate(allOf):
        validator.iter_errors(spec_instance, subschema)


def anyOf(validator, anyOf, spec_instance):

    for index, subschema in enumerate(anyOf):
        errs = False
        try:
            validator.iter_errors(spec_instance, subschema)
        except Exception as exp:
            errs = True

        if not errs:
            break

    else:
        raise Exception(
            '%r is not valid under any of the given schemas' % (spec_instance,)
        )


def type(validator, types, spec_instance):

    if isinstance(types, str):
        types = [types]

    if not any(validator.is_type(spec_instance, type) for type in types):
        raise Exception(
            'instance : %r doesn\'t match with any schema ' % (spec_instance)
        )


def title(validator, title, spec_instance):

    if not isinstance(title, str):
        raise Exception('title is not string')


class ValidatorType(object):

    validators = {
        u'items': items,
        u'minLength': minLength,
        u'maxLength': maxLength,
        u'enum': enum,
        u'properties': properties,
        u'required': required,
        u'allOf': allOf,
        u'anyOf': anyOf,
        u'type': type,
        u'title': title
    }
