# -*- coding: utf-8 -*-


class ClassProperty(property):
    """
    class property decorator
    """

    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class __IterableConstantsMeta__(type):
    def __iter__(self):
        """__iter__ providing a generator of all public attr"""
        for attr in dir(self):
            if not (attr.startswith("__") or attr == "ALL"):
                yield getattr(self, attr)


class IterableConstants(object):
    __metaclass__ = __IterableConstantsMeta__

    @ClassProperty
    @classmethod
    def ALL(cls):
        """
        Get the list of all attributes
        """
        return [attr for attr in cls]


class REQUEST(object):
    """Request related constants"""

    class SCHEME(IterableConstants):
        """
        Connection schemes
        """

        HTTP = "http"
        HTTPS = "https"

    class AUTH_TYPE(IterableConstants):
        """
        Types of auth
        """

        NONE = "none"
        BASIC = "basic"
        JWT = "jwt"

    class METHOD(IterableConstants):
        """
        Request methods
        """

        DELETE = "delete"
        GET = "get"
        POST = "post"
        PUT = "put"
