import click
import os

from .utils import highlight_text

file_dir = "calm/secrets"
file_helper = "calm/secrets/{}.txt"


def create_secret(name, value):
    """Creates the secret"""

    file_location = file_helper.format(name)
    if os.path.exists(file_location):
        click.echo(highlight_text("Secret Already present !!!\nTry to update secret\n"))
        return

    with open(file_location, "w+") as file:
        file.write(value)

    click.echo(highlight_text("\nSecret created !!! \n"))


def get_secrets():
    """List the secrets"""

    avl_files = os.listdir(file_dir)
    for file in avl_files:
        fname = file[: file.index(".")]
        click.echo(highlight_text(fname))


def delete_secret(name):
    """Deletes the secret"""

    file_location = file_helper.format(name)
    if os.path.exists(file_location):
        os.remove(file_location)
        click.echo(highlight_text("\nSecret deleted !!!\n"))

    else:
        click.echo(highlight_text("\nSecret not present !!!\n"))


def update_secret(name, value):
    """Updates the secret"""

    file_location = file_helper.format(name)
    if os.path.exists(file_location):
        with open(file_location, "w+") as file:
            file.write(value)
        click.echo(highlight_text("\nSecret updated !!!\n"))

    else:
        click.echo(highlight_text("\nSecret not present !!!\n"))


def find_secret(name):
    """ Gives you the value stored correponding to secret"""

    file_location = file_helper.format(name)
    if os.path.exists(file_location):
        with open(file_location, "r") as file:
            return file.read()

    else:
        raise Exception("No secret found !!!")
