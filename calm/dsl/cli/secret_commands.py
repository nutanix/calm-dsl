import click

from .main import get, create, update, delete
from .utils import highlight_text
from .secrets import create_secret, get_secrets, delete_secret, update_secret

# TODO Apply --type = local/server parameter
@create.command("secret")
@click.argument("name", nargs=1)
@click.option("--value", prompt=True, hide_input=True, confirmation_prompt=True, help="Value for secret")
@click.pass_obj
def _create_secret(obj, name, value):
    """Creates the secret

    NAME is the alias for your secret
    """

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want any pass_phrase associated with secret")),
        default="n",
    )

    pass_phrase = click.prompt("Passphrase") if choice[0] == "y" else None
    create_secret(name, value, pass_phrase)


@get.command("secrets")
@click.pass_obj
def _get_secrets(obj):
    """List the secrets """

    get_secrets()


@delete.command("secret")
@click.argument("name", nargs=1)
@click.pass_obj
def _delete_secret(obj, name):
    """Delete a secret"""

    delete_secret(name)


@update.command("secret")
@click.argument("name", nargs=1)
@click.option("--value", prompt=True, hide_input=True, confirmation_prompt=True)
@click.pass_obj
def _update_secret(obj, name, value):
    """Update the secret

    NAME is the alias for your secret
    """

    choice = click.prompt(
        "\n{}(y/n)".format(highlight_text("Want any pass_phrase associated with secret")),
        default="n",
    )

    pass_phrase = click.prompt("Passphrase") if choice[0] == "y" else None
    update_secret(name, value, pass_phrase)
