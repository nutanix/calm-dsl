import inspect
from ruamel import yaml
from click.testing import CliRunner
from functools import wraps
import uuid
import os
import pytest
import json
import traceback

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


# Note these paths are reltive to provider test directory
BP_FILE_PATH_LINUX = "test_bp_creation/_test_bp_linux_os_example.py"
BP_FILE_PATH_WINDOWS = "test_bp_creation/_test_bp_windows_os_example.py"
PROVIDER_SPEC_FILE_PATH = "test_bp_creation/provider_spec.yaml"


def run_test(
    input,
    cli_assertions,
    spec_assertions,
    cli_false_assertions,
    spec_false_assertions,
    provider_type="AHV_VM",
    bp_file_path=None,
    provider_spec_file_path=None,
):

    runner = CliRunner()
    command = "create provider_spec --type={}".format(provider_type)

    sep = "\n"
    input = sep.join(input)

    result = runner.invoke(cli, command, input=input)

    if result.exit_code:
        cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
        LOG.debug(
            "Cli Response: {}".format(
                json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
            )
        )
        LOG.debug(
            "Traceback: \n{}".format("".join(traceback.format_tb(result.exc_info[2])))
        )
        pytest.fail("Create provider_spec command failed")
    output = str(result.output)

    # Spec separator
    spec_sep_str = cli_assertions[0]

    ind = output.index(spec_sep_str)
    ind = ind + len(spec_sep_str)

    cli_output = output[:ind]
    spec_output = output[ind:]

    # Check for assertions in cli and spec outputs
    for entry in cli_assertions:
        assert cli_output.find(entry) > 0, "{} not present in cli_ouput".format(entry)

    for entry in spec_assertions:
        assert spec_output.find(entry) > 0, "{} not present in spec_ouput".format(entry)

    for entry in cli_false_assertions:
        assert cli_output.find(entry) < 0, "{} is present in cli_ouput".format(entry)

    for entry in spec_false_assertions:
        assert spec_output.find(entry) < 0, "{} is present in spec_ouput".format(entry)

    # Will try for bp creation, if dsl file and provider_spec_file is given
    if not (bp_file_path and provider_spec_file_path):
        if not bp_file_path:
            LOG.error("BP file path not found")

        if not provider_spec_file_path:
            LOG.error("Provider Spec file path not found")
        return

    for filepath in [bp_file_path, provider_spec_file_path]:
        if not os.path.exists(filepath):
            raise ValueError("file {} not found".format(filepath))

    # Getting the data stored in provider spec file
    with open(provider_spec_file_path, "r") as f:
        old_spec_data = f.read()

    # Overwriting spec output to provider spec file
    with open(provider_spec_file_path, "w") as f:
        f.write(spec_output)

    try:
        bp_name = "test_bp_create_{}".format(str(uuid.uuid4())[-10:])
        command = "create bp --file={} --name={}".format(bp_file_path, bp_name)

        # Try bp creation
        LOG.info("Creating bp {}".format(bp_name))
        result = runner.invoke(cli, command)
        command_output = result.output.lower()
        assert command_output.find("error") < 0, "Error occured in bp creation"
        LOG.info("Success")
        LOG.debug("Response : {}".format(result.output))

        # Delete created bp
        LOG.info("Deleting bp {}".format(bp_name))
        command = "delete bp {}".format(bp_name)
        result = runner.invoke(cli, command)

        assert result.exit_code == 0
        LOG.info("Success")
        LOG.debug("Response : {}".format(result.output))

    finally:
        # Rewriting the old data
        with open(provider_spec_file_path, "w") as f:
            f.write(old_spec_data)


def provider_decorator(provider_type="AHV_VM"):
    def decorate_method(func):
        @wraps(func)
        def cls_test_runner(*arg, **kwargs):

            func_name = func.__name__
            prefix = "test_"

            test_input_file_name = func_name[len(prefix) :] + ".yaml"  # noqa
            file_mod_location = inspect.getsourcefile(func)

            # Note For spec having windows os , pass os_type as function paramter
            sig = inspect.signature(func)
            sig_parameter = sig.parameters.get("os_type", None)

            if not sig_parameter:
                os_type = "Linux"
            else:
                os_type = sig_parameter.default

            if os_type not in ["Linux", "Windows"]:
                raise ValueError("os_type is not valid")

            bp_file_path = (
                BP_FILE_PATH_LINUX if os_type == "Linux" else BP_FILE_PATH_WINDOWS
            )
            provider_spec_file_path = PROVIDER_SPEC_FILE_PATH
            test_input_file_path = test_input_file_name

            try:
                module_path = file_mod_location[: file_mod_location.rindex("/")]
            except Exception:
                module_path = ""

            if module_path:
                test_input_file_path = "{}/{}".format(module_path, test_input_file_path)
                bp_file_path = "{}/{}".format(module_path, bp_file_path)
                provider_spec_file_path = "{}/{}".format(
                    module_path, provider_spec_file_path
                )

            with open(test_input_file_path, "r") as f:
                spec = yaml.safe_load(f.read())

            input = spec.get("input", [])
            cli_assertions = spec.get("cli_assertions", [])
            spec_assertions = spec.get("spec_assertions", [])
            cli_false_assertions = spec.get("cli_false_assertions", [])
            spec_false_assertions = spec.get("spec_false_assertions", [])

            run_test(
                input,
                cli_assertions,
                spec_assertions,
                cli_false_assertions,
                spec_false_assertions,
                provider_type,
                bp_file_path,
                provider_spec_file_path,
            )

        return cls_test_runner

    return decorate_method


def plugin_test(provider_type="AHV_VM"):
    def decorate_class(Cls):
        method_decorator = provider_decorator(provider_type)

        for key, value in list(vars(Cls).items()):
            if callable(value):
                setattr(Cls, key, method_decorator(value))

        return Cls

    return decorate_class
