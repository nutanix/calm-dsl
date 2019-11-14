from calm.dsl.providers import get_provider_interface


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
