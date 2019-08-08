import click
import json

from calm.dsl.providers import get_provider_interface


Provider = get_provider_interface()


# Implements Provider interface for EXISTING_VM
class ExistingVmProvider(Provider):

    package_name = __name__
    provider_type = "EXISTING_VM"
    spec_template_file = "existing_vm_provider_spec.yaml.jinja2"

    def create_spec(cls):
        create_spec()


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)


def create_spec():

    addr = click.prompt("Enter the address :", default="")
    spec = {"type": "PROVISION_EXISTING_MACHINE", "address": addr}

    click.secho("\nCreate spec\n", underline=True)
    click.echo(highlight_text(json.dumps(spec, sort_keys=True, indent=4)))
