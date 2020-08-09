class CalmAccount:
    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class NutanixPC:
        def __new__(cls, *args, **kwargs):
            return _account(*args, **kwargs)

    class Nutanix:
        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

    class VMWare:
        def __new__(cls, *args, **kwargs):
            return _account(*args, **kwargs)


def _account(name):
    account = {}
    account["name"] = name
    account["kind"] = "account"
    return account
