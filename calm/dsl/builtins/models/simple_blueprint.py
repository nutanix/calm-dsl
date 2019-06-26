from .entity import EntityType, Entity
from .validator import PropertyValidator

from .profile import profile
from .deployment import deployment
from .substrate import substrate
from .service import service
from .package import package
from .ref import ref

# Simple Blueprint


class SimpleBlueprintType(EntityType):
    __schema_name__ = "SimpleBlueprint"
    __openapi_type__ = "app_simple_blueprint"
    __has_dag_target__ = False

    def get_task_target(cls):
        return

    def get_bp_dict(cls):

        # Get simple blueprint dictionary
        cdict = cls.get_dict()

        # Create blueprint objects

        credential_definition_list = cdict["credentials"]

        # Init Profile
        pro = profile(name=cls.__name__ + "Profile")
        app_profile = pro.get_dict()
        app_profile["variable_list"] = cdict["variables"]
        app_profile["action_list"] = cdict["action_list"]
        app_profile_list = [app_profile]

        service_definition_list = []
        package_definition_list = []
        substrate_definition_list = []

        for sd in cdict["deployments"]:

            # Init service dict
            s = service(name=sd["name"] + "Service", description=sd["description"])
            sdict = s.get_dict()
            sdict["variable_list"] = sd["variable_list"]
            for action in sd["action_list"]:
                if action["name"].startswith("__") and action["name"].endswith("__"):
                    continue
                sdict["action_list"].append(action)
            sdict["depends_on_list"] = sd["depends_on_list"]
            for dep in sdict["depends_on_list"]:
                dep["kind"] = "app_service"

            # Init package dict
            p = package(name=sd["name"] + "Package")
            p.services = [ref(s)]
            pdict = p.get_dict()
            for action in sd["action_list"]:
                if action["name"] == "__install__":
                    pdict["options"]["install_runbook"] = action["runbook"]
                elif action["name"] == "__uninstall__":
                    pdict["options"]["uninstall_runbook"] = action["runbook"]

            # Init Substrate dict
            sub = substrate(
                name=sd["name"] + "Substrate",
                provider_type=sd["provider_type"],
                provider_spec=sd["provider_spec"],
                readiness_probe=sd["readiness_probe"],
                os_type=sd["os_type"],
            )
            subdict = sub.get_dict()
            for action in sd["action_list"]:
                if action["name"] == "__pre_create__":
                    action["name"] = sub.ALLOWED_FRAGMENT_ACTIONS["__pre_create__"]

                    for task in action["runbook"]["task_definition_list"]:
                        if task["target_any_local_reference"]:
                            task["target_any_local_reference"] = {
                                "kind": "app_substrate",
                                "name": subdict["name"],
                            }

                    subdict["action_list"].append(action)

                elif action["name"] == "__post_delete__":
                    action["name"] = sub.ALLOWED_FRAGMENT_ACTIONS["__post_delete__"]

                    for task in action["runbook"]["task_definition_list"]:
                        if task["target_any_local_reference"]:
                            task["target_any_local_reference"] = {
                                "kind": "app_substrate",
                                "name": subdict["name"],
                            }

                    subdict["action_list"].append(action)

            # Init deployment dict
            d = deployment(
                name=sd["name"],
                min_replicas=sd["min_replicas"],
                max_replicas=sd["max_replicas"],
            )
            d.packages = [ref(p)]
            d.substrate = ref(sub)
            ddict = d.get_dict()

            # Add items
            service_definition_list.append(sdict)
            package_definition_list.append(pdict)
            substrate_definition_list.append(subdict)

            app_profile["deployment_create_list"].append(ddict)

        blueprint_resources = {
            "service_definition_list": service_definition_list,
            "package_definition_list": package_definition_list,
            "substrate_definition_list": substrate_definition_list,
            "credential_definition_list": credential_definition_list,
            "app_profile_list": app_profile_list,
        }

        spec = {
            "name": cls.__name__,
            "description": cls.__doc__ or "",
            "resources": blueprint_resources,
        }

        metadata = {"spec_version": 1, "kind": "blueprint", "name": cls.__name__}

        blueprint = {"metadata": metadata, "spec": spec}

        return blueprint


class SimpleBlueprintValidator(PropertyValidator, openapi_type="app_simple_blueprint"):
    __default__ = None
    __kind__ = SimpleBlueprintType


def simple_blueprint(**kwargs):
    name = getattr(SimpleBlueprintType, "__schema_name__")
    bases = (Entity,)
    return SimpleBlueprintType(name, bases, kwargs)


SimpleBlueprint = simple_blueprint()
