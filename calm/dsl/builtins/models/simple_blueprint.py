from .entity import EntityType, Entity
from .validator import PropertyValidator

from .profile import profile
from .deployment import deployment
from .simple_pod_deployment import simple_pod_deployment
from .provider_spec import provider_spec as get_provider_spec
from .substrate import substrate
from .service import service
from .package import package
from .ref import ref
from .action import action as Action

# Simple Blueprint


class SimpleBlueprintType(EntityType):
    __schema_name__ = "SimpleBlueprint"
    __openapi_type__ = "app_simple_blueprint"
    __has_dag_target__ = False

    def get_task_target(cls):
        return

    def make_bp_dict(cls, categories=None):

        deployments = getattr(cls, "deployments", [])

        pod_deployments = []
        normal_deployments = []
        for dep in deployments:
            if dep.deployment_spec and dep.service_spec:
                pod_dep = simple_pod_deployment(
                    name=getattr(dep, "name", "") or dep.__name__,
                    service_spec=dep.service_spec,
                    deployment_spec=dep.deployment_spec,
                    dependencies=dep.dependencies,
                )

                pod_deployments.append(pod_dep)
                for key, value in dep.__dict__.items():
                    if isinstance(value, Action):
                        setattr(pod_dep, key, value)

            else:
                normal_deployments.append(dep)

        # Removing pod deployments from the deployments
        setattr(cls, "deployments", normal_deployments)

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
        published_service_definition_list = []

        for sd in cdict["deployments"]:

            # Init service dict
            s = service(name=sd["name"] + "Service", description=sd["description"])
            sdict = s.get_dict()
            sdict["variable_list"] = sd["variable_list"]

            compulsory_actions = sdict.pop("action_list", [])
            existing_system_actions = []
            sdict["action_list"] = []  # Initializing by empty list
            for action in sd["action_list"]:
                if action["name"].startswith("__") and action["name"].endswith("__"):
                    if action["name"] in s.ALLOWED_SYSTEM_ACTIONS:
                        action["name"] = s.ALLOWED_SYSTEM_ACTIONS[action["name"]]
                        action["type"] = "system"
                        action["critical"] = True
                        existing_system_actions.append(action["name"])
                    else:
                        continue
                sdict["action_list"].append(action)

            # Adding compulsory action action, if not supplied by user
            for action in compulsory_actions:
                if action["name"] not in existing_system_actions:
                    sdict["action_list"].append(action)

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
                provider_spec=get_provider_spec(sd["provider_spec"]),
                readiness_probe=sd["readiness_probe"],
                os_type=sd["os_type"],
            )
            subdict = sub.get_dict()

            for action in sd["action_list"]:
                if action["name"] == "__pre_create__":
                    action["name"] = sub.ALLOWED_FRAGMENT_ACTIONS["__pre_create__"]
                    action["type"] = "fragment"

                    for task in action["runbook"]["task_definition_list"]:
                        if task["target_any_local_reference"]:
                            task["target_any_local_reference"] = {
                                "kind": "app_substrate",
                                "name": subdict["name"],
                            }

                    subdict["action_list"].append(action)

                elif action["name"] == "__post_delete__":
                    action["name"] = sub.ALLOWED_FRAGMENT_ACTIONS["__post_delete__"]
                    action["type"] = "fragment"

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

            # Setting the deployment level dependencies
            ddict["depends_on_list"] = sd["depends_on_list"]

            # Add items
            service_definition_list.append(sdict)
            package_definition_list.append(pdict)
            substrate_definition_list.append(subdict)

            app_profile["deployment_create_list"].append(ddict)

        for pdep in pod_deployments:
            pod_dict = pdep.extract_deployment()
            for sd in pod_dict["service_definition_list"]:
                sdict = sd.get_dict()
                service_definition_list.append(sdict)

            for pd in pod_dict["package_definition_list"]:
                pdict = pd.get_dict()
                package_definition_list.append(pdict)

            for sub in pod_dict["substrate_definition_list"]:
                subdict = sub.get_dict()
                substrate_definition_list.append(subdict)

            for psd in pod_dict["published_service_definition_list"]:
                psddict = psd.get_dict()
                published_service_definition_list.append(psddict)

            for dep in pod_dict["deployment_definition_list"]:
                depdict = dep.get_dict()
                app_profile["deployment_create_list"].append(depdict)

        blueprint_resources = {
            "service_definition_list": service_definition_list,
            "package_definition_list": package_definition_list,
            "substrate_definition_list": substrate_definition_list,
            "credential_definition_list": credential_definition_list,
            "app_profile_list": app_profile_list,
            "published_service_definition_list": published_service_definition_list,
        }

        spec = {
            "name": cls.__name__,
            "description": cls.__doc__ or "",
            "resources": blueprint_resources,
        }

        metadata = {
            "spec_version": 1,
            "kind": "blueprint",
            "name": cls.__name__,
            "categories": categories,
        }

        blueprint = {"metadata": metadata, "spec": spec}

        return blueprint

    def make_single_vm_bp_dict(cls):

        bp_dict = cls.make_bp_dict()

        if len(bp_dict["spec"]["resources"]["substrate_definition_list"]) > 1:
            return None

        subdict = bp_dict["spec"]["resources"]["substrate_definition_list"][0]
        subdict["readiness_probe"] = {"disable_readiness_probe": True}

        if bp_dict["metadata"]["categories"]:
            bp_dict["metadata"]["categories"]["TemplateType"] = "Vm"
        else:
            bp_dict["metadata"]["categories"] = {"TemplateType": "Vm"}

        return bp_dict


class SimpleBlueprintValidator(PropertyValidator, openapi_type="app_simple_blueprint"):
    __default__ = None
    __kind__ = SimpleBlueprintType


def simple_blueprint(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return SimpleBlueprintType(name, bases, kwargs)


SimpleBlueprint = simple_blueprint()
