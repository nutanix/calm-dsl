from asyncio import sleep
import shutil
import os
from unittest import result, runner
import pytest
import uuid
from calm.dsl.cli import main as cli
from calm.dsl.store.version import Version
from distutils.version import LooseVersion as LV
from click.testing import CliRunner

CALM_VERSION = Version.get_version("Calm")
NORMAL_RUNBOOK_FILE_PATH = "tests/sample_runbooks/simple_runbook.py"
EXECUTION_NAME_RUNBOOK_FILE_PATH = "tests/sample_runbooks/execution_name_runbook.py"


@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("4.3.0"),
    reason="execution_name is supported in Calm v4.3.0+",
)
class TestExecutionNameRunbook:
    def setup_method(self):
        """Setup method to initialize created runbooks list"""
        self.created_rb_list = []

    def teardown_method(self):
        """Teardown method to delete created runbooks"""
        runner = CliRunner()
        for rb_name in self.created_rb_list:
            result = runner.invoke(cli, ["delete", "runbook", rb_name])
            assert result.exit_code == 0
        self.created_rb_list = []

    def _create_runbook(self, file_path, name):
        """Helper method to create a runbook"""
        runner = CliRunner()
        command = [
            "create",
            "runbook",
            "--file={}".format(file_path),
            "--name={}".format(name),
            "--description='Testing DSL Runbook with execution name functionality'",
            "--force",
        ]

        result = runner.invoke(cli, command)
        if result.exit_code:
            pytest.fail(f"Runbook creation failed: {result.output}")
        return result

    def _compile_runbook(self, file_path):
        """Helper method to compile a runbook"""
        runner = CliRunner()
        command = ["compile", "runbook", "-f", file_path]

        result = runner.invoke(cli, command)
        if result.exit_code:
            pytest.fail(f"Runbook compilation failed: {result.output}")
        return result

    def _decompile_runbook(self, rb_name):
        """Helper method to decompile a runbook"""
        runner = CliRunner()
        command = ["decompile", "runbook", rb_name]
        result = runner.invoke(cli, command)
        if result.exit_code:
            pytest.fail(f"Runbook decompilation failed: {result.output}")
        return result

    def cleanup_decompiled_directory(self, decompiled_dir_path):
        """Helper method to cleanup decompiled directory"""
        if os.path.exists(decompiled_dir_path):
            try:
                shutil.rmtree(decompiled_dir_path)
                print(f"Successfully removed directory: {decompiled_dir_path}")
            except Exception as e:
                print(f"Failed to remove directory {decompiled_dir_path}: {e}")

    def _run_runbook(self, rb_name, execution_name=None, input=None):
        """Helper method to run a runbook"""
        runner = CliRunner()
        command = ["run", "runbook", rb_name]
        if execution_name:
            command.append(f"--execution-name={execution_name}")

        if input:
            result = runner.invoke(cli, command, input=input)
        else:
            result = runner.invoke(cli, command)
        if result.exit_code:
            pytest.fail(f"Runbook execution failed: {result.output}")
        return result

    def test_runbook_with_execution_name(self):
        """Test creating a runbook with execution_name"""
        runner = CliRunner()
        rb_name = "test_with_exec_name_rb_" + str(uuid.uuid4())[-10:]
        self.created_rb_list.append(rb_name)

        # Create the runbook
        result = self._create_runbook(
            EXECUTION_NAME_RUNBOOK_FILE_PATH,
            rb_name,
        )
        assert result.exit_code == 0, f"Runbook creation failed: {result.output}"

        # Decompile the runbook
        decompile_result = self._decompile_runbook(rb_name)
        assert (
            decompile_result.exit_code == 0
        ), f"Runbook decompilation failed: {decompile_result.output}"
        decompiled_file_path = f"{rb_name}/runbook.py"
        with open(decompiled_file_path, "r") as f:
            decompiled_content = f.read()
            assert (
                "execution_name" in decompiled_content
            ), "execution_name should appear in the decompiled runbook"
            assert (
                "@@{calm_runbook_name}@@_custom_name" in decompiled_content
            ), "execution_name value should appear in the decompiled runbook"

        # Cleanup decompiled directory
        self.cleanup_decompiled_directory(rb_name)

        # Compile the runbook
        result = self._compile_runbook(EXECUTION_NAME_RUNBOOK_FILE_PATH)

        assert result.exit_code == 0, f"Runbook compilation failed: {result.output}"
        generated_json = result.output
        assert (
            '"execution_name": "@@{calm_runbook_name}@@_custom_name"' in generated_json
        ), "execution_name should be empty when not set"

        # Run runbook with no name execution_name
        result = self._run_runbook(rb_name, input="\n\n")
        assert result.exit_code == 0, f"Runbook execution failed: {result.output}"

        assert (
            "@@{calm_runbook_name}@@_custom_name" in result.output
        ), "func arg execution name should appear in the output"

        # Run runbook with different execution_name as cli arg
        result = self._run_runbook(
            rb_name, execution_name="custom_execution_name", input="\n\n"
        )
        assert result.exit_code == 0, f"Runbook execution failed: {result.output}"

        assert (
            "@@{calm_runbook_name}@@_custom_name" not in result.output
        ), "func arg execution name should not appear in the output"

    def test_runbook_without_execution_name(self):
        """Test creating a runbook without execution_name"""
        runner = CliRunner()
        rb_name = "test_without_exec_name_rb" + str(uuid.uuid4())[-10:]
        self.created_rb_list.append(rb_name)

        # Create the runbook
        result = self._create_runbook(
            NORMAL_RUNBOOK_FILE_PATH,
            rb_name,
        )
        assert result.exit_code == 0, f"Runbook creation failed: {result.output}"

        # Decompile the runbook
        decompile_result = self._decompile_runbook(rb_name)
        assert (
            decompile_result.exit_code == 0
        ), f"Runbook decompilation failed: {decompile_result.output}"
        decompiled_file_path = f"{rb_name}/runbook.py"
        with open(decompiled_file_path, "r") as f:
            decompiled_content = f.read()
            assert (
                "execution_name" not in decompiled_content
            ), "execution_name should not appear in the decompiled runbook"

        # Cleanup decompiled directory
        self.cleanup_decompiled_directory(rb_name)

        # Compile the runbook
        result = self._compile_runbook(NORMAL_RUNBOOK_FILE_PATH)

        assert result.exit_code == 0, f"Runbook compilation failed: {result.output}"
        generated_json = result.output
        assert (
            '"execution_name": ""' in generated_json
        ), "execution_name should be empty when not set"

        # Run runbook with execution_name no input
        result = self._run_runbook(rb_name, input="\n\n")
        assert result.exit_code == 0, f"Runbook execution failed: {result.output}"

        assert (
            "Execution name (Optional) for the Runbook Run" in result.output
        ), "Execution name prompt should appear in the output"

        # Run runbook with execution_name cli arg
        result = self._run_runbook(
            rb_name, execution_name="custom_execution_name", input="\n"
        )
        assert result.exit_code == 0, f"Runbook execution failed: {result.output}"
