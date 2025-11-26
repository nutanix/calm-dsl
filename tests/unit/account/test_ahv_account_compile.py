import pytest
from unittest.mock import patch, MagicMock
from distutils.version import LooseVersion as LV

from calm.dsl.builtins.models.account_resources import AccountResources
from calm.dsl.builtins.models.ahv_account import AhvAccountType
from calm.dsl.constants import ACCOUNT
from calm.dsl.store.version import Version
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class TestAhvAccountCompile:
    """Test class for AHV Account compile functionality"""

    def test_ahv_account_basic_auth(self):
        """Test AHV account compilation with basic auth (username/password)"""
        with patch(
            "calm.dsl.builtins.models.ahv_account.is_compile_secrets", return_value=True
        ):

            account = AccountResources.Ntnx(
                username="test_user",
                password="test_password",
                server="test.server.com",
                port="9440",
            )

            compiled = account.compile()

            # Check basic properties
            assert compiled["username"] == "test_user"
            assert compiled["server"] == "test.server.com"
            assert compiled["port"] == "9440"

            # Check password is properly formatted
            assert "password" in compiled
            assert compiled["password"]["value"] == "test_password"
            assert compiled["password"]["attrs"]["is_secret_modified"] is True

            # Service account should not be present
            assert "service_account" not in compiled

            current_version = Version.get_version("Calm")
            if LV(current_version) >= LV(ACCOUNT.SERVICE_ACCOUNT.FEATURE_MIN_VERSION):
                assert compiled["cred_type"] == ACCOUNT.CRED_TYPE.BASIC_AUTH
            else:
                assert compiled.get("cred_type") is None

    def test_ahv_account_without_secrets_compilation(self):
        """Test AHV account compilation when secrets are not compiled"""
        with patch(
            "calm.dsl.builtins.models.ahv_account.is_compile_secrets",
            return_value=False,
        ):

            account = AccountResources.Ntnx(
                username="test_user",
                password="test_password",
                server="test.server.com",
                port="9440",
            )

            compiled = account.compile()

            # Check that secret values are empty when not compiling secrets
            assert compiled["password"]["value"] == ""
            assert compiled["password"]["attrs"]["is_secret_modified"] is True

    # Tests for service account features - require version >= 4.3.0

    @pytest.mark.skipif(
        LV(Version.get_version("Calm"))
        < LV(ACCOUNT.SERVICE_ACCOUNT.FEATURE_MIN_VERSION),
        reason="Service account feature not available in this version",
    )
    @pytest.mark.service_account
    def test_ahv_account_service_account_auth(self):
        """Test AHV account compilation with service account auth"""
        with patch(
            "calm.dsl.builtins.models.ahv_account.is_compile_secrets", return_value=True
        ), patch("calm.dsl.store.version.Version.get_version", return_value="4.3.0"):

            account = AccountResources.Ntnx(
                service_account_api_key="test_api_key",
                server="test.server.com",
                port="9440",
            )

            compiled = account.compile()

            # Check basic properties
            assert compiled["server"] == "test.server.com"
            assert compiled["port"] == "9440"

            # Check service account is properly formatted
            assert "service_account" in compiled
            assert compiled["service_account"]["value"] == "test_api_key"
            assert compiled["service_account"]["attrs"]["is_secret_modified"] is True

            # Check cred_type is set to service_account
            assert compiled["cred_type"] == ACCOUNT.CRED_TYPE.SERVICE_ACCOUNT

            # Password should not be present
            assert "password" not in compiled

    @pytest.mark.skipif(
        LV(Version.get_version("Calm"))
        < LV(ACCOUNT.SERVICE_ACCOUNT.FEATURE_MIN_VERSION),
        reason="Service account feature not available in this version",
    )
    @pytest.mark.service_account
    def test_ahv_account_without_secrets_compilation_with_service_account(self):
        """Test AHV account compilation when secrets are not compiled (with service account)"""
        with patch(
            "calm.dsl.builtins.models.ahv_account.is_compile_secrets",
            return_value=False,
        ), patch("calm.dsl.store.version.Version.get_version", return_value="4.3.0"):

            account = AccountResources.Ntnx(
                service_account_api_key="test_api_key",
                server="test.server.com",
                port="9440",
            )

            compiled = account.compile()

            # Check that service account value is empty when not compiling secrets
            assert compiled["service_account"]["value"] == ""
            assert compiled["service_account"]["attrs"]["is_secret_modified"] is True

            # Check cred_type is set to service_account
            assert compiled["cred_type"] == ACCOUNT.CRED_TYPE.SERVICE_ACCOUNT
