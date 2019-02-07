class _PropertyValidatorBase:
    subclasses = {}

    def __init_subclass__(cls, openapi_type, **kwargs):
        super().__init_subclass__(**kwargs)

        if openapi_type is not None:
            # register validator plugins
            cls.subclasses[openapi_type] = cls


def get_property_validators():
    return _PropertyValidatorBase.subclasses


class PropertyValidator(_PropertyValidatorBase, openapi_type=None):

    __default__ = None
    __kind__ = None

    @classmethod
    def get_default(cls):
        return cls.__default__

    @classmethod
    def get_kind(cls):
        return cls.__kind__

    @classmethod
    def _validate_item(cls, value):
        kind = cls.get_kind()
        if not isinstance(value, kind):
            raise TypeError('{} is not of type {}'.format(value, kind))

    @staticmethod
    def _validate_list(values):
        if not isinstance(values, list):
            raise TypeError('{} is not of type {}'.format(values, list))

    @classmethod
    def validate(cls, value):

        default = cls.get_default()
        is_array = True if isinstance(default, list) else False

        if not is_array:
            cls._validate_item(value)
        else:
            cls._validate_list(value)
            for v in value:
                cls._validate_item(v)


# built-in validators

class StringValidator(PropertyValidator, openapi_type="string"):

    __default__ = ''
    __kind__ = str


class StringListValidator(StringValidator, openapi_type="strings"):

    __default__ = []


class IntValidator(PropertyValidator, openapi_type="integer"):

    __default__ = 0
    __kind__ = int


class BoolValidator(PropertyValidator, openapi_type="boolean"):

    __default__ = False
    __kind__ = bool


class DictValidator(PropertyValidator, openapi_type="dict"):

    __default__ = {}
    __kind__ = dict
