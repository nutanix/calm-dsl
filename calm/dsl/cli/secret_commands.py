import click

from .main import get, create, update, delete, clear
from .secrets import (
    create_secret,
    get_secrets,
    delete_secret,
    update_secret,
    clear_secrets,
)

# TODO Apply --type = local/server parameter
@create.command("secret")
@click.argument("name", nargs=1)
@click.option(
    "--value",
    "-v",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Value for secret",
)
@click.pass_obj
def _create_secret(obj, name, value):
    """Creates the secret

    NAME is the alias for your secret
    """

    create_secret(name, value)


@get.command("secrets")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only sceret names."
)
@click.pass_obj
def _get_secrets(obj, quiet):
    """List the secrets """

    get_secrets(quiet)


@delete.command("secret")
@click.argument("name", nargs=1)
@click.pass_obj
def _delete_secret(obj, name):
    """Delete a secret"""

    delete_secret(name)


@update.command("secret")
@click.argument("name", nargs=1)
@click.option("--value", "-v", prompt=True, hide_input=True, confirmation_prompt=True)
@click.pass_obj
def _update_secret(obj, name, value):
    """Update the secret

    NAME is the alias for your secret
    """

    update_secret(name, value)


@clear.command("secrets")
@click.pass_obj
def _clear_secrets(obj):
    """Delete alll the secrets stored in the local db"""

    clear_secrets()
