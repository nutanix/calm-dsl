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
def _create_secret(name, value):
    """Creates a secret"""

    create_secret(name, value)


@get.command("secrets")
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only sceret names."
)
def _get_secrets(quiet):
    """Get secrets """

    get_secrets(quiet)


@delete.command("secret")
@click.argument("name", nargs=1)
def _delete_secret(name):
    """Deletes a secret"""

    delete_secret(name)


@update.command("secret")
@click.argument("name", nargs=1)
@click.option("--value", "-v", prompt=True, hide_input=True, confirmation_prompt=True)
def _update_secret(name, value):
    """Updates a secret

    NAME is the alias for your secret
    """

    update_secret(name, value)


@clear.command("secrets")
def _clear_secrets():
    """Delete all the secrets stored in the local db"""

    clear_secrets()
