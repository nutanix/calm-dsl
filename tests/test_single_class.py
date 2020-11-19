from calm.dsl.builtins import Service, Package
from calm.dsl.builtins import CalmVariable as Var
from calm.dsl.builtins import action

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


def test_service_invalid_multiple_inheritance():

    with pytest.raises(TypeError):

        class Invalid(Service, Package):
            pass

        pytest.fail("Multiple inheritance allowed for different entity types")


def test_service_valid_multiple_inheritance():
    class Loyal(Service):

        lfoo = Var("lbar")

        @action
        def loyal_action():
            pass

    class Animal(Service):

        afoo = Var("abar")

        @action
        def animal_action():
            pass

    class Dog(Animal, Loyal):
        pass

    Dog.compile()


def test_service_invalid_name():

    with pytest.raises(SystemExit):

        from calm.dsl.builtins import Service

        class Service(Service):
            pass

        pytest.fail("Internal name allowed")


if __name__ == "__main__":
    test_service_invalid()
    test_service_invalid_setattr()
