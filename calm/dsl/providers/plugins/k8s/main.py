from calm.dsl.providers import get_provider_interface
from calm.dsl.api import get_resource_api, get_api_client

Provider = get_provider_interface()


# Implements Provider interface for K8S_POD
class K8sProvider(Provider):

    provider_type = "K8S_POD"
    package_name = __name__
    spec_template_file = "k8s_provider_spec.yaml.jinja2"

    @classmethod
    def validate_spec(cls, spec):
        # TODO - Add validation for K8S spec
        pass

    @classmethod
    def get_api_obj(cls):
        """returns object to call kubernetes provider specific apis"""

        client = get_api_client()
        return Kubernetes(client.connection)


class Kubernetes:
    def __init__(self, connection):
        self.connection = connection

    def karbon_clusters(self, params=None):
        Obj = get_resource_api(
            resource_type="kubernetes/v1/karbon/clusters",
            connection=self.connection,
        )
        Obj.ROOT = "api/calm/v3.0.a1"
        return Obj.list(params=params)
