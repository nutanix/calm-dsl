import copy

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

    def decompile(cls, cdict):

        attrs = {}
        display_map = copy.deepcopy(cls.display_map)
        display_map = {v: k for k, v in display_map.items()}

        # reversing display map values
        for k, v in cdict.items():
            attrs.setdefault(display_map[k], v)

        # recursive decompile
        validator_dict = cls.validators
        for k, v in attrs.items():
            validator, is_array = validator_dict[k]

            if hasattr(validator, "__kind__"):
                entity_type = validator.__kind__

            else:
                # Case for recursive Object Dict
                entity_type = validator

            new_value = None
            if hasattr(entity_type, "decompile"):
                if is_array:
                    new_value = []
                    if not isinstance(v, list):
                        raise Exception("Value not of type list")

                    for val in v:
                        new_value.append(entity_type.decompile(val))

                else:
                    new_value = entity_type.decompile(v)

            else:
                # validation for existing classes(str, dict etc.)
                # validation for existing classes(str, dict etc.)
                if is_array:
                    new_value = []
                    for val in v:
                        if not isinstance(val, entity_type):
                            raise TypeError(
                                "Value {} is not of type {}".format(val, entity_type)
                            )

                        new_value.append(entity_type(val))

                else:
                    new_value = entity_type(v)

            attrs[k] = new_value

        return attrs

    def _validate_item(self, value):
        if not isinstance(value, dict):
            raise TypeError("{} is not of type {}".format(value, "dict"))
        new_value = self.__class__(self.validators, self.defaults, self.display_map)
        for k, v in value.items():
            new_value[k] = v
        return new_value

    def validate(self, value, is_array):
        if not is_array:
            if isinstance(value, type(None)):
                return
            return self._validate_item(value)

        else:
            if not isinstance(value, list):
                raise TypeError("{} is not of type {}".format(value, "list"))

            res_value = []
            for entity in value:
                new_value = self._validate_item(entity)
                res_value.append(new_value)
            return res_value


class ObjectValidator(PropertyValidator, openapi_type="object"):
    __default__ = ObjectDict
    __kind__ = ObjectDict
