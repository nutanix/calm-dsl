from calm.dsl.providers import get_provider_interface


Provider = get_provider_interface()


# Implements Provider interface for EXISTING_VM
class ExistingVmProvider(Provider):

    package_name = __name__
    provider_type = "EXISTING_VM"
    spec_template_file = "existing_vm_provider_spec.yaml.jinja2"
