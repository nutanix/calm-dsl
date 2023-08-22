import sys
from distutils.version import LooseVersion as LV

from .entity import EntityType, Entity, EntityTypeBase, EntityDict
from .validator import PropertyValidator
from .readiness_probe import readiness_probe
from .provider_spec import provider_spec
from .ahv_vm import AhvVmType, ahv_vm
from .client_attrs import update_dsl_metadata_map, get_dsl_metadata_map
from .metadata_payload import get_metadata_obj
from .helper import common as common_helper

from calm.dsl.config import get_context
from calm.dsl.constants import CACHE, PROVIDER_ACCOUNT_TYPE_MAP
from calm.dsl.store import Cache
from calm.dsl.store import Version
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


# Substrate


class SubstrateDict(EntityDict):
    @classmethod
    def pre_validate(cls, vdict, name, value, parent=None):
        if name == "readiness_probe":
            if isinstance(value, dict):
                rp_validator, is_array = vdict[name]
                rp_cls_type = rp_validator.get_kind()
                return vdict, rp_cls_type(None, (Entity,), value)

        return vdict, value


class SubstrateType(EntityType):
    __schema_name__ = "Substrate"
    __openapi_type__ = "app_substrate"
    __prepare_dict__ = SubstrateDict

    ALLOWED_FRAGMENT_ACTIONS = {
        "__pre_create__": "pre_action_create",
        "__post_delete__": "post_action_delete",
    }

    def get_profile_environment(cls):
        """returns the profile environment, if substrate has been defined in blueprint file"""

        cls_bp = common_helper._walk_to_parent_with_given_type(cls, "BlueprintType")
        environment = {}
        if cls_bp:
            for cls_profile in cls_bp.profiles:
                for cls_deployment in cls_profile.deployments:
                    if cls_deployment.substrate.name != str(cls):
                        continue

                    environment = getattr(cls_profile, "environment", {})
                    if environment:
                        LOG.debug(
                            "Found environment {} associated to app-profile {}".format(
                                environment.get("name"), cls_profile
                            )
                        )
                    break
        return environment

    def get_referenced_account_uuid(cls):
        """
            SUBSTRATE GIVEN UNDER BLUEPRINT
        If calm-version < v3.2.0:
            1. account_reference is not available at substrate-level, So need to read from project only
        If calm-version >= 3.2.0:
            1. account_reference is available at substrate-level
                1.a: If env is given at profile-level, then account must be whitelisted in environment
                1.b: If env is not given at profile-level, then account must be whitelisted in project
            2. If account_reference is not available at substrate-level
                2.a: If env is given at profile-level, return provider account in env
                2.b: If env is not given at profile-level, return provider account in project

            SUBSTRATE GIVEN UNDER ENVIRONMENT
        If calm-version < v3.2.0:
            1. account_reference is not available at substrate-level, So need to read from project only
        If calm-version >= 3.2.0:
            1. account_reference is available at substrate-level
                1. account must be filtered at environment
            2. If account_reference is not available at substrate-level
                2.a: return provider account whitelisted in environment

        """

        provider_account = getattr(cls, "account", {})
        calm_version = Version.get_version("Calm")
        provider_type = getattr(cls, "provider_type")
        provider_account_type = PROVIDER_ACCOUNT_TYPE_MAP.get(provider_type, "")
        if not provider_account_type:
            return ""

        # Fetching project data
        project_cache_data = common_helper.get_cur_context_project()
        project_name = project_cache_data.get("name")
        project_accounts = project_cache_data.get("accounts_data", {}).get(
            provider_account_type, []
        )
        if not project_accounts:
            LOG.error(
                "No '{}' account registered to project '{}'".format(
                    provider_account_type, project_name
                )
            )
            sys.exit(-1)

        # If substrate is defined in blueprint file
        cls_bp = common_helper._walk_to_parent_with_given_type(cls, "BlueprintType")
        if cls_bp:
            environment = {}
            for cls_profile in cls_bp.profiles:
                for cls_deployment in cls_profile.deployments:
                    if cls_deployment.substrate.name != str(cls):
                        continue

                    environment = getattr(cls_profile, "environment", {})
                    if environment:
                        LOG.debug(
                            "Found environment {} associated to app-profile {}".format(
                                environment.get("name"), cls_profile
                            )
                        )
                    break

            # If environment is given at profile level
            if environment:
                environment_cache_data = Cache.get_entity_data_using_uuid(
                    entity_type=CACHE.ENTITY.ENVIRONMENT, uuid=environment["uuid"]
                )
                if not environment_cache_data:
                    LOG.error(
                        "Environment {} not found. Please run: calm update cache".format(
                            environment["name"]
                        )
                    )
                    sys.exit(-1)

                accounts = environment_cache_data.get("accounts_data", {}).get(
                    provider_account_type, []
                )
                if not accounts:
                    LOG.error(
                        "Environment '{}' has no '{}' account.".format(
                            environment_cache_data.get("name", ""),
                            provider_account_type,
                        )
                    )
                    sys.exit(-1)

                # If account given at substrate, it should be whitelisted in environment
                if provider_account and provider_account["uuid"] != accounts[0]["uuid"]:
                    LOG.error(
                        "Account '{}' not filtered in environment '{}'".format(
                            provider_account["name"],
                            environment_cache_data.get("name", ""),
                        )
                    )
                    sys.exit(-1)

                # If provider_account is not given, then fetch from env
                elif not provider_account:
                    provider_account = {
                        "name": accounts[0]["name"],
                        "uuid": accounts[0]["uuid"],
                    }

            # If environment is not given at profile level
            else:
                # if provider_account is given, it should be part of project
                if not project_accounts:
                    LOG.error(
                        "No '{}' account registered to project '{}'".format(
                            provider_account_type, project_name
                        )
                    )
                    sys.exit(-1)

                if (
                    provider_account
                    and provider_account["uuid"] not in project_accounts
                ):
                    LOG.error(
                        "Account '{}' not filtered in project '{}'".format(
                            provider_account["name"], project_name
                        )
                    )
                    sys.exit(-1)

                # Else take first account in project
                elif not provider_account:
                    provider_account = {"uuid": project_accounts[0], "kind": "account"}

        # If substrate defined inside environment
        cls_env = common_helper._walk_to_parent_with_given_type(cls, "EnvironmentType")
        if cls_env:
            infra = getattr(cls_env, "providers", [])
            whitelisted_account = {}
            for _pdr in infra:
                if _pdr.type == PROVIDER_ACCOUNT_TYPE_MAP[provider_type]:
                    whitelisted_account = _pdr.account_reference.get_dict()
                    break

            if LV(calm_version) >= LV("3.2.0"):
                if provider_account and provider_account[
                    "uuid"
                ] != whitelisted_account.get("uuid", ""):
                    LOG.error(
                        "Account '{}' not filtered in environment '{}'".format(
                            provider_account["name"], str(cls_env)
                        )
                    )
                    sys.exit(-1)

                elif not whitelisted_account:
                    LOG.error(
                        "No account is filtered in environment '{}'".format(
                            str(cls_env)
                        )
                    )
                    sys.exit(-1)

                elif not provider_account:
                    provider_account = whitelisted_account

        # If version is less than 3.2.0, then it should use account from poroject only, OR
        # If no account is supplied, will take 0th account in project (in both case of blueprint/environment)
        if not provider_account:
            provider_account = {"uuid": project_accounts[0], "kind": "account"}

        return provider_account["uuid"]

    def compile(cls):

        cdict = super().compile()

        readiness_probe_dict = {}
        if "readiness_probe" in cdict and cdict["readiness_probe"]:
            readiness_probe_dict = cdict["readiness_probe"]
            if hasattr(readiness_probe_dict, "compile"):
                readiness_probe_dict = readiness_probe_dict.compile()
        else:
            readiness_probe_dict = readiness_probe().compile()

        # Fill out os specific details if not found
        if cdict["os_type"] == "Linux":
            if not readiness_probe_dict.get("connection_type", ""):
                readiness_probe_dict["connection_type"] = "SSH"

            if not readiness_probe_dict.get("connection_port", ""):
                readiness_probe_dict["connection_port"] = 22

            if not readiness_probe_dict.get("connection_protocol", ""):
                readiness_probe_dict["connection_protocol"] = ""

        else:
            if not readiness_probe_dict.get("connection_type", ""):
                readiness_probe_dict["connection_type"] = "POWERSHELL"

            if not readiness_probe_dict.get("connection_port", ""):
                readiness_probe_dict["connection_port"] = 5985

            if not readiness_probe_dict.get("connection_protocol", ""):
                readiness_probe_dict["connection_protocol"] = "http"

        if cdict.get("vm_recovery_spec", {}) and cdict["type"] != "AHV_VM":
            LOG.error(
                "Recovery spec is supported only for AHV_VM substrate (given {})".format(
                    cdict["type"]
                )
            )
            sys.exit("Unknown attribute vm_recovery_spec given")

        # Handle cases for empty readiness_probe and vm_recovery_spec
        if cdict["type"] == "AHV_VM":
            if not readiness_probe_dict.get("address", ""):
                readiness_probe_dict[
                    "address"
                ] = "@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@"

            if cdict.get("vm_recovery_spec", {}):
                _vrs = cdict.pop("vm_recovery_spec", None)
                if _vrs:
                    cdict["create_spec"] = ahv_vm(
                        name=_vrs.vm_name, resources=_vrs.vm_override_resources
                    )
                    cdict["recovery_point_reference"] = _vrs.recovery_point

        elif cdict["type"] == "EXISTING_VM":
            if not readiness_probe_dict.get("address", ""):
                readiness_probe_dict["address"] = "@@{ip_address}@@"

        elif cdict["type"] == "AWS_VM":
            if not readiness_probe_dict.get("address", ""):
                readiness_probe_dict["address"] = "@@{public_ip_address}@@"

        elif cdict["type"] == "K8S_POD":  # Never used (Omit after discussion)
            readiness_probe_dict["address"] = ""
            cdict.pop("editables", None)

        elif cdict["type"] == "AZURE_VM":
            if not readiness_probe_dict.get("address", ""):
                readiness_probe_dict[
                    "address"
                ] = "@@{platform.publicIPAddressList[0]}@@"

        elif cdict["type"] == "VMWARE_VM":
            if not readiness_probe_dict.get("address", ""):
                readiness_probe_dict["address"] = "@@{platform.ipAddressList[0]}@@"

        elif cdict["type"] == "GCP_VM":
            if not readiness_probe_dict.get("address", ""):
                readiness_probe_dict[
                    "address"
                ] = "@@{platform.networkInterfaces[0].accessConfigs[0].natIP}@@"

        else:
            raise Exception("Un-supported vm type :{}".format(cdict["type"]))

        if not cdict.get("vm_recovery_spec", {}):
            cdict.pop("vm_recovery_spec", None)

        # Adding min defaults in vm spec required by each provider
        if not cdict.get("create_spec"):

            # TODO shift them to constants file
            provider_type_map = {
                "AWS_VM": "aws",
                "VMWARE_VM": "vmware",
                "AHV_VM": "nutanix_pc",  # Accounts of type nutanix are not used after 2.9
                "AZURE_VM": "azure",
                "GCP_VM": "gcp",
            }

            if cdict["type"] in provider_type_map:
                if cdict["type"] == "AHV_VM":
                    # UI expects defaults. Jira: https://jira.nutanix.com/browse/CALM-20134
                    if not cdict.get("create_spec"):
                        cdict["create_spec"] = {"resources": {"nic_list": []}}

                else:
                    # Getting the account_uuid for each provider
                    # Getting the metadata obj
                    metadata_obj = get_metadata_obj()
                    project_ref = metadata_obj.get("project_reference") or dict()

                    # If project not found in metadata, it will take project from config
                    ContextObj = get_context()
                    project_config = ContextObj.get_project_config()
                    project_name = project_ref.get("name", project_config["name"])

                    project_cache_data = Cache.get_entity_data(
                        entity_type=CACHE.ENTITY.PROJECT, name=project_name
                    )
                    if not project_cache_data:
                        LOG.error(
                            "Project {} not found. Please run: calm update cache".format(
                                project_name
                            )
                        )
                        sys.exit(-1)

                    # Registered accounts
                    project_accounts = project_cache_data["accounts_data"]
                    provider_type = provider_type_map[cdict["type"]]
                    account_uuids = project_accounts.get(provider_type, [])
                    if not account_uuids:
                        LOG.error(
                            "No {} account registered in project '{}'".format(
                                provider_type, project_name
                            )
                        )
                        sys.exit(-1)

                    # Adding default spec
                    cdict["create_spec"] = {
                        "resources": {"account_uuid": account_uuids[0]}
                    }

                    # Template attribute should be present for vmware spec
                    if cdict["type"] == "VMWARE_VM":
                        cdict["create_spec"]["template"] = ""

        # Modifying the editable object
        provider_spec_editables = cdict.pop("editables", {})
        cdict["editables"] = {}

        if provider_spec_editables:
            cdict["editables"]["create_spec"] = provider_spec_editables

        # Popping out the editables from readiness_probe
        readiness_probe_editables = readiness_probe_dict.pop("editables_list", [])
        if readiness_probe_editables:
            cdict["editables"]["readiness_probe"] = {
                k: True for k in readiness_probe_editables
            }

        # In case we have read provider_spec from a yaml file, validate that we have consistent values for
        # Substrate.account (if present) and account_uuid in provider_spec (if present).
        # The account_uuid mentioned in provider_spec yaml should be a registered PE under the Substrate.account PC

        substrate_account_uuid = cls.get_referenced_account_uuid()
        spec_account_uuid = ""
        try:
            spec_account_uuid = cdict["create_spec"]["resources"]["account_uuid"]
        except (AttributeError, TypeError, KeyError):
            pass

        if substrate_account_uuid:
            account_cache_data = Cache.get_entity_data_using_uuid(
                entity_type="account", uuid=substrate_account_uuid
            )
            if not account_cache_data:
                LOG.error(
                    "Account (uuid={}) not found. Please update cache".format(
                        substrate_account_uuid
                    )
                )
                sys.exit(-1)
            account_name = account_cache_data["name"]

            if spec_account_uuid:
                if cdict["type"] == "AHV_VM":
                    if (
                        not account_cache_data.get("data", {})
                        .get("clusters", {})
                        .get(spec_account_uuid)
                    ):
                        LOG.error(
                            "cluster account_uuid (uuid={}) used in the provider spec is not found to be registered"
                            " under the Nutanix PC account {}. Please update cache".format(
                                spec_account_uuid, account_name
                            )
                        )
                        sys.exit(-1)

                elif cdict["type"] != "EXISTING_VM":
                    if spec_account_uuid != substrate_account_uuid:
                        LOG.error(
                            "Account '{}'(uuid='{}') not matched with account_uuid used in provider-spec (uuid={})".format(
                                account_name, substrate_account_uuid, spec_account_uuid
                            )
                        )
                        sys.exit(-1)

            else:
                # if account_uuid is not available add it
                if cdict["type"] == "AHV_VM":

                    # default is first cluster account
                    account_uuid = list(account_cache_data["data"]["clusters"].keys())[
                        0
                    ]

                    _cs = cdict["create_spec"]

                    if isinstance(_cs, AhvVmType):
                        # NOTE: We cann't get subnet_uuid here, as it involved parent reference
                        subnet_name = ""
                        cluster_name = _cs.cluster or ""
                        _nics = _cs.resources.nics
                        if cluster_name:
                            account_uuid = common_helper.get_pe_account_using_pc_account_uuid_and_cluster_name(
                                pc_account_uuid=substrate_account_uuid,
                                cluster_name=cluster_name,
                            )
                        else:
                            for _nic in _nics:
                                _nic_dict = _nic.subnet_reference.get_dict()
                                if _nic_dict["cluster"] and not common_helper.is_macro(
                                    _nic_dict["name"]
                                ):
                                    subnet_name = _nic_dict["name"]
                                    cluster_name = _nic_dict["cluster"]
                                    break

                            # calm_version = Version.get_version("Calm")
                            # if LV(calm_version) >= LV("3.5.0") and not cluster_name:
                            #    raise Exception("Unable to infer cluster for vm")
                            if subnet_name:
                                account_uuid = common_helper.get_pe_account_uuid_using_pc_account_uuid_and_nic_data(
                                    pc_account_uuid=substrate_account_uuid,
                                    subnet_name=subnet_name,
                                    cluster_name=cluster_name,
                                )

                        # Assigning the pe account uuid to ahv vm resources
                        _cs.resources.account_uuid = account_uuid

                    else:
                        subnet_uuid = ""
                        _nics = _cs.get("resources", {}).get("nic_list", [])

                        for _nic in _nics:
                            _nu = _nic["subnet_reference"].get("uuid", "")
                            if _nu and not common_helper.is_macro(_nu):
                                subnet_uuid = _nu
                                break

                        if subnet_uuid:
                            account_uuid = common_helper.get_pe_account_uuid_using_pc_account_uuid_and_subnet_uuid(
                                pc_account_uuid=substrate_account_uuid,
                                subnet_uuid=subnet_uuid,
                            )

                        cdict["create_spec"]["resources"]["account_uuid"] = account_uuid

        # Add account uuid for non-ahv providers
        if cdict["type"] not in ["EXISTING_VM", "AHV_VM", "K8S_POD"]:
            cdict["create_spec"]["resources"]["account_uuid"] = substrate_account_uuid

        cdict.pop("account_reference", None)
        cdict["readiness_probe"] = readiness_probe_dict

        return cdict

    def pre_compile(cls):
        """Adds Ahvvm data to substrate metadata"""
        super().pre_compile()

        # Adding mapping for substrate class in case of AHV provider
        types = EntityTypeBase.get_entity_types()
        AhvVmType = types.get("AhvVm", None)

        provider_spec = cls.provider_spec
        if isinstance(provider_spec, AhvVmType):
            ui_name = getattr(cls, "name", "") or cls.__name__
            sub_metadata = get_dsl_metadata_map([cls.__schema_name__, ui_name])

            vm_dsl_name = provider_spec.__name__
            vm_display_name = getattr(provider_spec, "name", "") or vm_dsl_name

            sub_metadata[AhvVmType.__schema_name__] = {
                vm_display_name: {"dsl_name": vm_dsl_name}
            }

            update_dsl_metadata_map(
                cls.__schema_name__, entity_name=ui_name, entity_obj=sub_metadata
            )

    @classmethod
    def pre_decompile(mcls, cdict, context=[], prefix=""):

        # Handle provider_spec
        cdict = super().pre_decompile(cdict, context, prefix=prefix)
        cdict["create_spec"] = provider_spec(cdict["create_spec"])

        if "__name__" in cdict:
            cdict["__name__"] = "{}{}".format(prefix, cdict["__name__"])

        return cdict

    @classmethod
    def decompile(mcls, cdict, context=[], prefix=""):

        if cdict["type"] == "K8S_POD":
            LOG.error("Decompilation support for pod deployments is not available.")
            sys.exit(-1)

        cls = super().decompile(cdict, context=context, prefix=prefix)

        provider_spec = cls.provider_spec
        if cls.provider_type == "AHV_VM":
            context = [cls.__schema_name__, getattr(cls, "name", "") or cls.__name__]
            vm_cls = AhvVmType.decompile(provider_spec, context=context, prefix=prefix)

            cls.provider_spec = vm_cls

        return cls

    def get_task_target(cls):
        return cls.get_ref()


class SubstrateValidator(PropertyValidator, openapi_type="app_substrate"):
    __default__ = None
    __kind__ = SubstrateType


def substrate(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return SubstrateType(name, bases, kwargs)


Substrate = substrate()
