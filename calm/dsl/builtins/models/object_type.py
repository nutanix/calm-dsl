from .validator import PropertyValidator
from .entity import EntityDict


class ObjectDict(EntityDict):
    __is_object__ = True

    def __init__(self, validators, defaults):
        self.validators = validators
        self.defaults = defaults
        for k, v in self.defaults.items():
            self[k] = v()
        super().__init__(validators)

    def get_default(self, is_array):
        return self.__class__(self.validators, self.defaults)

    def __call__(self):
        return self.__class__(self.validators, self.defaults)


class ObjectValidator(PropertyValidator, openapi_type="object"):
    __default__ = ObjectDict
    __kind__ = ObjectDict
