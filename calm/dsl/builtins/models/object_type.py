from copy import deepcopy

from .validator import PropertyValidator
from .entity import EntityDict


class ObjectDict(EntityDict):
    __is_object__ = True

    def get_default(self, is_array):
        return self.__class__(self.validators)

    def __call__(self):
        return self.__class__(self.validators)

class ObjectValidator(PropertyValidator, openapi_type="object"):

    __default__ = ObjectDict
    __kind__ = ObjectDict
