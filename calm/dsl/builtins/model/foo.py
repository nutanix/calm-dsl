#!/usr/bin/env python3

"""
Playground area. TODO: Remove later
"""

from .validator import BoolValidator


class FooDict(OrderedDict):

    def __init__(self):
        self.valid_attrs = ["singleton"]

    def __setitem__(self, name, value):

        if not (name.startswith('__') and name.endswith('__')):
            if name not in self.valid_attrs:
                raise TypeError("Unknown attribute {} given".format(name))

        super().__setitem__(name, value)


class FooBase(type):

    @classmethod
    def __prepare__(mcls, name, bases, **kwargs):
        return FooDict()

    def __new__(mcls, name, bases, foodict):

        # Replace foodict to dict() before passing to super()
        cls = type.__new__(mcls, name, bases, dict(foodict))

        cls.__valid_attrs__ = foodict.valid_attrs

        setattr(type(cls), "singleton", BoolValidator())

        # print(mcls.__dict__)

        for k, v in mcls.__dict__.items():
            func = getattr(v, '__set_name__', None)
            if func is not None:
                func(mcls, k)

        return cls

    def __setattr__(cls, name, value):
        # print("{}->{}".format(name, value))

        if not (name.startswith('__') and name.endswith('__')):

            if name not in cls.__valid_attrs__:
                raise TypeError("Unknown attribute {} given".format(name))

            descr_obj = cls.__class__.__dict__.get(name, None)

            func = getattr(descr_obj, '__validate__', None)
            if func is not None:
                func(value)

        # Only way to set class attributes
        super().__setattr__(name, value)

    def __getattr__(cls, name):
        # TODO - Do some work. This would be called if __getattribute__ fails.
        raise TypeError("Unknown attribute {} given".format(name))


class Foo(metaclass=FooBase):
    pass
