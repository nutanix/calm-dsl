from calm.dsl.builtins import Service

import pytest


def test_service_invalid():

    with pytest.raises(TypeError):

        class MySQLService(Service):
            """sample mysql service specification"""

            foo = "bar"
            singleton = False

        print(MySQLService.json_dumps(pprint=True))

        # shouldn't get here
        pytest.fail("Invalid Service property (foo='bar') allowed")


def test_service_invalid_setattr():

    with pytest.raises(TypeError):

        class MySQLService(Service):
            """sample mysql service specification"""

            singleton = False
            tier = "db"

        MySQLService.foo = "bar"

        print(MySQLService.json_dumps(pprint=True))

        # shouldn't get here
        pytest.fail("Invalid Service property (foo='bar') allowed")


def test_service_valid_setattr():
    class MySQLService(Service):
        pass

    MySQLService.tier = "db"


if __name__ == "__main__":
    test_service_invalid()
    test_service_invalid_setattr()
