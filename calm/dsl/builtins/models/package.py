from .entity import EntityType, Entity
from .validator import PropertyValidator


# Package

class PackageType(EntityType):
    __schema_name__ = "Package"
    __openapi_type__ = "app_package"

    def compile(cls):

        cdict = super().compile()

        # TODO - fix this mess!
        # Custom package needs empty DAGs for install and uninstall runbooks

        if not cdict["type"] == "CUSTOM":
            return cdict


        def make_empty_dag_runbook(packge_name, rb_name, dag_task_name):

            rb_dict =  {
                "task_definition_list": [{
                    "target_any_local_reference": {
                        "kind": "app_package",
                        "name": package_name,
                    },
                    "name": dag_task_name,
                    "state": "ACTIVE",
                    "attrs": {
                        "edges": [],
                        "type": ""
                    },
                    "type": "DAG",
                }],

                "name": rb_name,
                "state": "ACTIVE",
                "main_task_local_reference": {
                    "kind": "app_task",
                    "name": dag_task_name,
                },
            }

            return rb_dict

        rb_name = "install_runbook_" + cls.__name__
        dag_task_name = "install_dag_task_" + cls.__name__
        package_name = cls.__name__
        install_runbook = make_empty_dag_runbook(package_name, rb_name, dag_task_name)

        rb_name = "uninstall_runbook_" + cls.__name__
        dag_task_name = "uninstall_dag_task_" + cls.__name__
        package_name = cls.__name__
        uninstall_runbook = make_empty_dag_runbook(package_name, rb_name, dag_task_name)

        cdict["options"]["install_runbook"] = install_runbook
        cdict["options"]["uninstall_runbook"] = uninstall_runbook

        return cdict


class PackageValidator(PropertyValidator, openapi_type="app_package"):
    __default__ = None
    __kind__ = PackageType


def package(**kwargs):
    name = getattr(PackageType, "__schema_name__")
    bases = (Entity, )
    return PackageType(name, bases, kwargs)


Package = package()
