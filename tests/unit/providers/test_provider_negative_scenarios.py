import os
import pytest

from calm.dsl.cli.providers import compile_provider
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def _test_compile_negative_scenarios(provider_file, error_substring):
    """
    Verifies whether appropriate exceptions are raised in error scenarios or not

    Args:
        provider_file (string): Path to the DSL file that needs to be compiled
        error_substring (string): Substring expected in the exception
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    try:
        compile_provider(os.path.join(dir_path, provider_file))
        error_msg = "Expected '{}' error. But got none".format(error_substring)
        LOG.error(error_msg)
        assert False, error_msg
    except SystemExit as ex:
        assert error_substring.lower() in str(ex).lower()


@pytest.mark.provider
@pytest.mark.parametrize(
    "provider_file, error_substring",
    [
        ("./dsl_files/provider_without_auth_schema.py", "Auth_schema is required"),
        (
            "./dsl_files/provider_without_variables_in_custom_ep_schema.py",
            "No variables specified",
        ),
        (
            "./dsl_files/provider_with_incorrect_infra_type.py",
            "Infra type should be one of",
        ),
        (
            "./dsl_files/provider_with_multiple_actions.py",
            "Atmost one verify action can be added for provider",
        ),
        (
            "./dsl_files/provider_with_incorrect_action_name.py",
            "Action should be named",
        ),
        (
            "./dsl_files/provider_with_incorrect_action_type.py",
            "action should be of type 'provider'",
        ),
        (
            "./dsl_files/provider_with_incorrect_ep_schema_type.py",
            "Endpoint Schema type should be one of",
        ),
        (
            "./dsl_files/provider_with_unexpected_ep_variables.py",
            "Cannot specify Variables",
        ),
    ],
)
def test_provider_compile_negative_scenarios(provider_file, error_substring):
    _test_compile_negative_scenarios(provider_file, error_substring)


@pytest.mark.provider
@pytest.mark.parametrize(
    "provider_file, error_substring",
    [
        (
            "./dsl_files/resource_type_with_incorrect_action_type.py",
            "ResourceType Action's type should be one of",
        ),
    ],
)
def test_resource_type_compile_negative_scenarios(provider_file, error_substring):
    _test_compile_negative_scenarios(provider_file, error_substring)
