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

        def make_install_runbook(cls, cdict):

            rb_name = "install_runbook_" + cls.__name__
            dag_task_name = "install_dag_task_" + cls.__name__
            package_name = cls.__name__

            count = 0
            install_tasks = cdict["install_tasks"]
            child_tasks_local_reference_list = []
            child_task_list = []
            for task in install_tasks:

                task_dict = task.compile()
                task_dict["name"] = "install_task_" + "{}".format(count) + cls.__name__
                count += 1

                task_dict["target_any_local_reference"] = {
                    "name": package_name,
                    "kind": "app_package",
                }

                child_task_ref = {"name": task_dict["name"], "kind": "app_task"}
                child_tasks_local_reference_list.append(child_task_ref)
                child_task_list.append(task_dict)

            # Construct DAG task with right references
            dag_task_dict = {
                "target_any_local_reference": {
                    "kind": "app_package",
                    "name": package_name,
                },
                "name": dag_task_name,
                "state": "ACTIVE",
                "attrs": {"edges": [], "type": ""},
                "type": "DAG",
                "child_tasks_local_reference_list": child_tasks_local_reference_list,
            }

            task_definition_list = [dag_task_dict] + child_task_list

            rb_dict = {
                "task_definition_list": task_definition_list,
                "name": rb_name,
                "state": "ACTIVE",
                "main_task_local_reference": {
                    "kind": "app_task",
                    "name": dag_task_name,
                },
            }

            return rb_dict

        install_runbook = make_install_runbook(cls, cdict)

        def make_empty_dag_runbook(packge_name, rb_name, dag_task_name):

            rb_dict = {
                "task_definition_list": [
                    {
                        "target_any_local_reference": {
                            "kind": "app_package",
                            "name": package_name,
                        },
                        "name": dag_task_name,
                        "state": "ACTIVE",
                        "attrs": {"edges": [], "type": ""},
                        "type": "DAG",
                    }
                ],
                "name": rb_name,
                "state": "ACTIVE",
                "main_task_local_reference": {
                    "kind": "app_task",
                    "name": dag_task_name,
                },
            }

            return rb_dict

        rb_name = "uninstall_runbook_" + cls.__name__
        dag_task_name = "uninstall_dag_task_" + cls.__name__
        package_name = cls.__name__
        uninstall_runbook = make_empty_dag_runbook(package_name, rb_name, dag_task_name)

        cdict["options"]["install_runbook"] = install_runbook
        cdict["options"]["uninstall_runbook"] = uninstall_runbook

        # Delete additional dsl keys
        # TODO - pop items based on schema flag
        del cdict["install_tasks"]

        return cdict


class PackageValidator(PropertyValidator, openapi_type="app_package"):
    __default__ = None
    __kind__ = PackageType


def package(**kwargs):
    name = getattr(PackageType, "__schema_name__")
    bases = (Entity,)
    return PackageType(name, bases, kwargs)


Package = package()
