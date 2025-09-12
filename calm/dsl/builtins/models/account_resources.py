import sys
import uuid
from copy import deepcopy
from distutils.version import LooseVersion as LV

from calm.dsl.builtins import (
    ahv_account,
    aws_account,
    aws_c2s_account,
    gcp_account,
    azure_account,
    vmware_account,
    k8s_karbon_account,
    k8s_vanilla_account,
    custom_provider_account,
    credential_provider_account,
    CalmVariable,
    Ref,
)

from calm.dsl.constants import CACHE, VARIABLE, ACCOUNT
from calm.dsl.store import Cache
from calm.dsl.store.version import Version
from calm.dsl.builtins.models.helper.common import is_not_right_ref
from .utils import is_compile_secrets

from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class AccountResources:
    class Ntnx:
        def __new__(
            cls,
            username=None,
            password=None,
            server=None,
            port=None,
            service_account_api_key=None,
        ):

            kwargs = {}

            if server is not None:
                kwargs["server"] = server
            if port is not None:
                kwargs["port"] = str(port)
            if username is not None:
                kwargs["username"] = username
            if password is not None:
                kwargs["password"] = password

            # Only pass service_account if the version of Calm >= 4.3.0
            calm_version = Version.get_version("Calm")
            if LV(calm_version) >= LV(ACCOUNT.SERVICE_ACCOUNT.FEATURE_MIN_VERSION):
                if service_account_api_key is not None:
                    kwargs["service_account"] = service_account_api_key
            return ahv_account(**kwargs)

    class Aws:
        def __new__(cls, access_key_id, secret_access_key, regions=[]):
            return aws_account(
                access_key_id=access_key_id,
                secret_access_key=secret_access_key,
                regions=regions,
            )

    class Aws_C2s:
        def __new__(
            cls,
            account_address,
            client_key,
            client_certificate,
            role,
            mission,
            agency,
            regions=[],
        ):
            return aws_c2s_account(
                account_address=account_address,
                client_key=client_key,
                client_certificate=client_certificate,
                role=role,
                mission=mission,
                agency=agency,
                regions=regions,
            )

    class Gcp:
        def __new__(
            cls,
            project_id,
            private_key_id,
            private_key,
            client_email,
            token_uri,
            client_id,
            auth_uri,
            auth_provider_cert_url,
            client_cert_url,
            gke_config={},
            public_images=[],
            regions=[],
        ):
            return gcp_account(
                project_id=project_id,
                private_key_id=private_key_id,
                private_key=private_key,
                client_email=client_email,
                token_uri=token_uri,
                client_id=client_id,
                auth_uri=auth_uri,
                auth_provider_cert_url=auth_provider_cert_url,
                client_cert_url=client_cert_url,
                regions=regions,
                public_images=public_images,
                gke_config=gke_config,
            )

    class Azure:
        def __new__(
            cls,
            tenant_id,
            client_id,
            client_key,
            cloud,
            subscriptions=[],
            default_subscription="",
        ):
            return azure_account(
                tenant_id=tenant_id,
                client_id=client_id,
                client_key=client_key,
                cloud=cloud,
                subscriptions=subscriptions,
                default_subscription=default_subscription,
            )

    class Vmware:
        def __new__(
            cls, username, password, server, port, price_items, datacenter=None
        ):
            return vmware_account(
                username=username,
                password=password,
                server=server,
                port=str(port),
                datacenter=datacenter,
                price_items=price_items,
            )

    class K8s_Karbon:
        def __new__(cls, cluster):
            return k8s_karbon_account(cluster=cluster, type="karbon")

    class K8s_Vanilla:
        def __new__(cls, server, port, auth):
            return k8s_vanilla_account(
                auth=auth, server=server, port=str(port), type="vanilla"
            )

    class CredentialProvider:
        def __new__(cls, vault_uri, vault_token, resource_config, **kwargs):
            auth_schemas = [
                CalmVariable.Simple.string(name="vault_uri", value=vault_uri),
                CalmVariable.Simple.Secret.string(
                    name="vault_token", value=vault_token
                ),
            ]
            for _k, _v in kwargs.items():
                if isinstance(_v, str):
                    auth_schemas.append(CalmVariable.Simple.string(name=_k, value=_v))
                elif isinstance(_v, CalmVariable):
                    auth_schemas.append(_v)
                else:
                    LOG.error(
                        "Additional variables can be only of type string or CalmVariable object"
                    )
                    sys.exit("Invalid additional variable provided")

            return credential_provider_account(
                auth_schemas=auth_schemas,
                resource_config=resource_config,
            )

    class CustomProvider:
        def __new__(cls, provider, variable_dict, parent=None):

            if is_not_right_ref(provider, Ref.Provider):
                LOG.error("Provider should be instance of Ref.Provider")
                sys.exit("Provider should be instance of Ref.Provider")

            provider_cache = provider.compile()

            # provider_auth_schema_list = auth_schema_variables + endpoint_schema_variables + variables
            provider_auth_schema_list = deepcopy(provider_cache["auth_schema_list"])
            provider_auth_schema_list.extend(
                deepcopy(
                    provider_cache.get("endpoint_schema", {}).get("variable_list", [])
                )
            )
            provider_auth_schema_list.extend(
                deepcopy(provider_cache.get("variable_list", []))
            )

            # check if all the variables provided are present in provider's auth_schema_list
            provider_auth_schema_variables = [
                auth_var["label"].lower().replace(" ", "_")
                for auth_var in provider_auth_schema_list
            ]

            provider_auth_schema_variables.extend(
                [auth_var["name"] for auth_var in provider_auth_schema_list]
            )

            for auth_var in variable_dict:
                if auth_var not in provider_auth_schema_variables:
                    LOG.error("{} is not a valid variable".format(auth_var))
                    sys.exit("Invalid variable provided")

            for auth_schema_var in provider_auth_schema_list:
                auth_schema_var.pop("state", None)
                auth_schema_var.pop("message_list", None)
                auth_schema_var["uuid"] = str(uuid.uuid4())

                if (
                    auth_schema_var.get("options", {}).get("type")
                    == VARIABLE.OPTIONS.TYPE.HTTP
                ):
                    header_vars = auth_schema_var["options"]["attrs"].get("headers", [])
                    for header_var in header_vars:
                        header_var["uuid"] = str(uuid.uuid4())

                var_name = auth_schema_var["name"]
                var_type = auth_schema_var["type"]
                var_label = auth_schema_var["label"]
                label_dict_key = var_label.lower().replace(" ", "_")

                if not label_dict_key and not var_name:
                    continue

                if not is_compile_secrets() and var_type in VARIABLE.SECRET_TYPES:
                    auth_schema_var["value"] = ""
                elif var_name in variable_dict:
                    auth_schema_var["value"] = variable_dict[var_name]
                elif label_dict_key in variable_dict:
                    auth_schema_var["value"] = variable_dict[label_dict_key]
                elif auth_schema_var["is_mandatory"]:
                    LOG.error(
                        "{} is a mandatory variable".format(var_label or var_name)
                    )
                    sys.exit("Mandatory variable not provided")

                if var_type in VARIABLE.SECRET_TYPES:
                    auth_schema_var.pop("attrs")
                    auth_schema_var["attrs"] = {"is_secret_modified": True}

            provider_reference = {
                "kind": "provider",
                "uuid": provider_cache["uuid"],
                "name": provider_cache["name"],
            }

            return custom_provider_account(
                provider_reference=provider_reference,
                parent_reference=parent,
                variable_list=provider_auth_schema_list,
            )

    class NDBProvider:
        def __new__(cls, parent, variable_dict):

            parent_provider_type = Cache.get_entity_data(
                entity_type=CACHE.ENTITY.ACCOUNT, name=parent
            ).get("provider_type", None)

            if parent_provider_type != "nutanix_pc":
                LOG.error("Parent should be of type 'AHV'")
                sys.exit("Invalid parent value")

            ndb_provider = Ref.Provider(name="NDB")

            return AccountResources.CustomProvider(
                provider=ndb_provider, parent=parent, variable_dict=variable_dict
            )
