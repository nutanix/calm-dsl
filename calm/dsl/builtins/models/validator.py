from copy import deepcopy


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

    # @classmethod
    # def get_default(cls, is_array):
    #     return cls.__default__ if not is_array else []

    @classmethod
    def get_default(cls, is_array):
        default = None
        class_default = cls.__default__
        if not callable(class_default):
            default = lambda: deepcopy(class_default)  # noqa: E731
        else:
            default = class_default
        return default if not is_array else list

    @classmethod
    def get_kind(cls):
        return cls.__kind__

    @classmethod
    def _validate_item(cls, value):

        if isinstance(value, type(None)):
            return

        kind = cls.get_kind()
        # Value may be a class or an object
        # If not an class, check for metaclass for object's class(Ex: Provider Spec)
        if not (
            isinstance(value, kind)
            or isinstance(type(value), kind)
            or (hasattr(kind, "validate_dict") and (not kind.validate_dict(value)))
        ):
            raise TypeError("{} is not of type {}".format(value, kind))

    @staticmethod
    def _validate_list(values):
        if not isinstance(values, list):
            raise TypeError("{} is not of type {}".format(values, list))

    @classmethod
    def validate(cls, value, is_array):

        if not is_array:
            cls._validate_item(value)
        else:
            cls._validate_list(value)
            for v in value:
                cls._validate_item(v)

    # Note on __set__() interface:
    # Initial plan was to use PropertyValidator as descriptors and make use of the magical
    # __set__() interface to validate values.
    # The validator objects were set as attributes on metaclass so that the
    # __set__() interface which would call the right validator. But this does not work for
    # type objects (e.g. - class object) as these attributes cannot be assigned outside
    # its scope. More details in the else block below.

    # def __set__(self, instance, value):
    #     """ The below dict assignment does not work for type objects like classes as
    #     `cls.__dict__` is immutable and exposed through a `mappingproxy` which
    #     is read-only.

    #     `object.__setattr__(instance, name, value)` will also not work as this specifically
    #     checks if the first argument is a subclass of `object`. `instance` here would
    #     be a `type` object for class and hence this will fail.
    #     The check is there to prevent this method being used to modify built-in
    #     types (Carlo Verre hack).

    #     So, descriptors cannot work in current form on type objects as class
    #     attributes are stored as `mappingproxy` objects. So only
    #     `class.__setattr__` remains as an avenue for setting class attributes.

    #     Now, `setattr` works by looking for a data descriptor in
    #     `type(obj).__mro__`. If a data descriptor is found (i.e. if __set__ is defined),
    #     it calls `__set__` and exits.
    #     There is no way to avoid this, and uderstandably so, as this is the purpose
    #     of the magical `__set__` interface.

    #     But, as `class.__dict__` cannot be used to set attribute,
    #     `setattr(cls, self.name, value)` is the only way.
    #     Calling setattr inside this block will cause infinite recursion!
    #     Else block below has more details.

    #     """

    #     self.validate(value, is_array)

    #     # Does not work if instance is a type object.
    #     if not isinstance(instance, type):
    #         instance.__dict__[self.name] = value
    #         # This works fine.
    #     else:
    #         # setattr(instance, self.name, value)
    #         # This would call __set__ again and hence cause infinite recusion.

    #         # type.__setattr__(instance, self.name, value)
    #         # This would call __set__ again and hence cause infinite recusion.

    #         # instance.__dict__[self.name] = value
    #         # Item assignment for mappingproxy object is not allowed.

    #         # object.__setattr__(instance, self.name, value)
    #         # This does not work as `instance` is a type object.

    #         # Sorry, can't do anything!

    #         pass

    # To overcome this problem:
    # a __validator_dict__ dictionary is set on the metaclass which has the correct
    # validator type mappings based on property name and validator methods have
    # been made as classmethods.
    # These mappings are checked during class creation using a hook to
    # __prepare__() and during attribute assignmets by using a hook to __setattr__()
    # interfaces. More details in EntityType.__prepare__() methods.


# built-in validators


class StringValidator(PropertyValidator, openapi_type="string"):

    __default__ = str
    __kind__ = str


class IntValidator(PropertyValidator, openapi_type="integer"):

    __default__ = int
    __kind__ = int


class BoolValidator(PropertyValidator, openapi_type="boolean"):

    __default__ = bool
    __kind__ = bool


class DictValidator(PropertyValidator, openapi_type="dict"):

    __default__ = dict
    __kind__ = dict
