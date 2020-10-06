import pytest
import uuid
from click.testing import CliRunner

from calm.dsl.cli import main as cli


class TestSecretCommands:
    def test_secrets_list(self):
        runner = CliRunner()
        command = "get secrets"
        result = runner.invoke(cli, command)
        assert result.exit_code == 0
        if result.exit_code:
            pytest.fail("Secret List call failed")

    def test_secret_crud(self):

        runner = CliRunner()

        secret_name = "secret_{}".format(str(uuid.uuid4())[-10:])
        secret_val = "val_{}".format(str(uuid.uuid4())[-10:])
        command = "create secret {}".format(secret_name)

        input = "{}\n{}".format(secret_val, secret_val)

        # Creating a secret
        result = runner.invoke(cli, command, input=input)
        assert result.exit_code == 0

        # Get the presence of secret in list call
        command = "get secrets"
        result = runner.invoke(cli, command)
        assert result.exit_code == 0
        assert secret_name in result.output

        # Updating the secret
        secret_val = "val_{}".format(str(uuid.uuid4())[-10:])
        command = "update secret {}".format(secret_name)
        input = "{}\n{}".format(secret_val, secret_val)

        result = runner.invoke(cli, command, input=input)
        assert result.exit_code == 0

        # Deleting the secret
        command = "delete secret {}".format(secret_name)
        result = runner.invoke(cli, command)
        assert result.exit_code == 0

    def test_create_multiple_secret_with_same_name(self):
        """Creating multiple secrets with same name
        (Negative Test)
        """

        runner = CliRunner()

        secret_name = "secret_{}".format(str(uuid.uuid4())[-10:])
        secret_val = "val_{}".format(str(uuid.uuid4())[-10:])
        command = "create secret {}".format(secret_name)

        input = "{}\n{}".format(secret_val, secret_val)

        # Creating a secret
        result = runner.invoke(cli, command, input=input)
        assert result.exit_code == 0

        secret_val = "val_{}".format(str(uuid.uuid4())[-10:])
        input = "{}\n{}".format(secret_val, secret_val)

        # Creating same secret again
        result = runner.invoke(cli, command, input=input)
        assert result.exit_code == 0

        secret_val = "val_{}".format(str(uuid.uuid4())[-10:])
        input = "{}\n{}".format(secret_val, secret_val)

        # Deleting the secret
        command = "delete secret {}".format(secret_name)
        result = runner.invoke(cli, command)
        assert result.exit_code == 0
