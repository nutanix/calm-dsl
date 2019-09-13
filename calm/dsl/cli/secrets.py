import click

from .utils import highlight_text
from calm.dsl.builtins import _create_secret, _delete_secret, _update_secret, list_secrets, _find_secret


def create_secret(name, value, pass_phrase=""):
    """Creates the secret"""

    secrets = list_secrets()
    if name in secrets:
        click.echo(highlight_text("Secret Already present !!!\nTry to update secret\n"))
        return

    _create_secret(name, value, pass_phrase)
    click.echo(highlight_text("\nSecret created !!! \n"))


def get_secrets():
    """List the secrets"""

    avl_secrets = list_secrets()
    for secret in avl_secrets:
        click.echo(highlight_text(secret))


def delete_secret(name):
    """Deletes the secret"""

    secrets = list_secrets()
    if name not in secrets:
        click.echo(highlight_text("\nSecret not present !!!\n"))
        return

    _delete_secret(name)
    click.echo(highlight_text("\nSecret deleted !!!\n"))


def update_secret(name, value, pass_phrase):
    """Updates the secret"""

    secrets = list_secrets()
    if name not in secrets:
        click.echo(highlight_text("\nSecret not present !!!\n"))
        return

    _update_secret(name, value, pass_phrase)
    click.echo(highlight_text("\nSecret updated !!!\n"))


def find_secret(name, pass_phrase):
    """ Gives you the value stored correponding to secret"""

    secret_val = _find_secret(name, pass_phrase)
    return secret_val
