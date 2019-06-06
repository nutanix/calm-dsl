from .validator import PropertyValidator
from .entity import EntityDict


class ObjectDict(EntityDict):
    __is_object__ = True

    def __init__(self, validators, defaults, display_map):
        self.validators = validators
        self.defaults = defaults
        self.display_map = display_map
        self.__items_set__ = False
        super().__init__(validators)

    def get_default(self, is_array):
        return self.__class__(self.validators, self.defaults, self.display_map)

    def __call__(self):
        return self.__class__(self.validators, self.defaults, self.display_map)

    def __setitem__(self, name, value):
        self.__items_set__ = True
        super().__setitem__(name, value)

    def compile(self, cls):
        ret = {}
        if not self.__items_set__:
            return ret
        for key, value in self.defaults.items():
            value = self.get(key, value())
            if getattr(value, "__is_object__", False):
                ret[self.display_map[key]] = value.compile(self)
            else:
                ret[self.display_map[key]] = value
        return ret


class ObjectValidator(PropertyValidator, openapi_type="object"):
    __default__ = ObjectDict
    __kind__ = ObjectDict
