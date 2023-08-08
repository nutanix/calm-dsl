import sys
import uuid
from copy import deepcopy

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
)

from calm.dsl.constants import CACHE
from calm.dsl.store import Cache
from .helper.common import get_provider

from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class AccountResources:
    class Ntnx:
        def __new__(cls, username, password, server, port):
            return ahv_account(
                username=username, password=password, server=server, port=str(port)
            )

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
        def __new__(cls, provider, parent, variable_dict):

            variable_list_values = variable_dict

            provider_auth_schema_list = deepcopy(
                provider["spec"]["resources"]["auth_schema_list"]
            )

            # check if all the variables provided are present in provider's auth_schema_list
            provider_auth_schema_variables = [
                auth_var["label"].lower().replace(" ", "_")
                for auth_var in provider_auth_schema_list
            ]

            for auth_var in variable_dict:
                if auth_var not in provider_auth_schema_variables:
                    LOG.error("{} is not a valid variable")
                    sys.exit("Invalid variable provided")

            for auth_schema in provider_auth_schema_list:
                auth_schema["uuid"] = str(uuid.uuid4())
                auth_schema.pop("state")
                auth_schema["message_list"] = []

                label_dict_key = auth_schema["label"].lower().replace(" ", "_")

                if not label_dict_key:
                    continue

                if (label_dict_key not in variable_list_values) and (
                    auth_schema["is_mandatory"]
                ):
                    LOG.error("{} is a mandatory variable".format(label_dict_key))
                    sys.exit("Mandatory variable not provided")

                auth_schema["value"] = variable_list_values[label_dict_key]

                if auth_schema["type"] == "SECRET":
                    auth_schema.pop("attrs")
                    auth_schema["attrs"] = {"is_secret_modified": True}

            provider_reference = {
                "kind": "provider",
                "uuid": provider["metadata"]["uuid"],
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

            ndb_provider = get_provider(name="NDB")

            return AccountResources.CustomProvider(
                provider=ndb_provider, parent=parent, variable_dict=variable_dict
            )
