import json
import sys

from calm.dsl.log import get_logging_handle
from calm.dsl.constants import CLOUD_PROVIDER as PROVIDER

from .entity import EntityType, Entity
from .validator import PropertyValidator

LOG = get_logging_handle(__name__)


# Provider Endpoint Schema
class ProviderEndpointSchemaType(EntityType):
    __schema_name__ = "ProviderEndpointSchema"
    __openapi_type__ = "provider_endpoint_schema"

    def compile(cls):
        cdict = super().compile()

        schema_type = cdict.get("type", PROVIDER.ENDPOINT_KIND.NONE)
        if schema_type not in PROVIDER.ENDPOINT_KINDS:
            error = "Endpoint Schema type should be one of %s" % (
                json.dumps(PROVIDER.ENDPOINT_KINDS)
            )
            LOG.error(error)
            sys.exit(error)

        if schema_type != PROVIDER.ENDPOINT_KIND.CUSTOM:
            variable_list = cdict.pop("variable_list", None)
            if variable_list:
                error = "Cannot specify Variables for Endpoint Schema of type '%s'" % (
                    schema_type
                )
                LOG.error(error)
                sys.exit(error)
        else:
            variable_list = cdict.get("variable_list")
            if not variable_list:
                error = "No variables specified for Endpoint Schema of type '%s'. Note: " % (
                    schema_type
                ) + "If Endpoint Schema is not required, either remove endpoint_schema or use type '%s'" % (
                    PROVIDER.ENDPOINT_KIND.NONE
                )
                LOG.error(error)
                sys.exit(error)

        return cdict


class ProviderEndpointSchemaValidator(
    PropertyValidator, openapi_type="provider_endpoint_schema"
):
    __default__ = None
    __kind__ = ProviderEndpointSchemaType


def provider_endpoint_schema(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return ProviderEndpointSchemaType(name, bases, kwargs)


ProviderEndpointSchema = provider_endpoint_schema
NoneEndpointSchema = lambda: ProviderEndpointSchema(type=PROVIDER.ENDPOINT_KIND.NONE)
NutanixEndpointSchema = lambda: ProviderEndpointSchema(
    type=PROVIDER.ENDPOINT_KIND.NUTANIX_PC
)
VmwareEndpointSchema = lambda: ProviderEndpointSchema(
    type=PROVIDER.ENDPOINT_KIND.VMWARE
)
GCPEndpointSchema = lambda: ProviderEndpointSchema(type=PROVIDER.ENDPOINT_KIND.GCP)
AWSEndpointSchema = lambda: ProviderEndpointSchema(type=PROVIDER.ENDPOINT_KIND.AWS)
AzureEndpointSchema = lambda: ProviderEndpointSchema(type=PROVIDER.ENDPOINT_KIND.AZURE)
