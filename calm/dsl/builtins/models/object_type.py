from .validator import PropertyValidator
from .entity import EntityDict


class ObjectDict(EntityDict):
    __is_object__ = True

    def __init__(self, validators, defaults, display_map):
        self.validators = validators
        self.defaults = defaults
        self.display_map = display_map
        super().__init__(validators)

    def get_default(self, is_array):
        return self.__class__(self.validators, self.defaults, self.display_map)

    def __call__(self):
        return self.__class__(self.validators, self.defaults, self.display_map)

    def compile(self, cls):
        ret = {}
        for key, value in self.items():
            ret[self.display_map[key]] = value
        return ret


class ObjectValidator(PropertyValidator, openapi_type="object"):
    __default__ = ObjectDict
    __kind__ = ObjectDict
