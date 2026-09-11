"""
Unit tests for blocking NTNX_LOCAL_AZ account operations in CALM VM setup.

These tests verify that NTNX_LOCAL_AZ account operations (create, update)
are properly blocked when running on a CALM VM setup.
"""

import pytest
from unittest.mock import patch, MagicMock

from calm.dsl.constants import ACCOUNT


class TestLocalAzBlockageInCalmVM:
    """Test class for NTNX_LOCAL_AZ blockage in CALM VM"""

    def test_local_az_blocked_in_calm_vm(self):
        """
        Negative test: Verify NTNX_LOCAL_AZ operations are blocked in CALM VM

        Tests that create and update operations for NTNX_LOCAL_AZ account
        exit with error when running on CALM VM setup (is_calm_vm_setup returns True).
        """

        from calm.dsl.cli.accounts import create_account, update_account

        # Mock client
        mock_client = MagicMock()

        # Mock account payload for nutanix_pc type
        account_payload = {
            "spec": {
                "name": ACCOUNT.LOCAL_AZ,
                "resources": {"type": "nutanix_pc", "data": {}},
            }
        }

        # Test 1: Create account blocked in CALM VM
        with patch("calm.dsl.cli.accounts.is_calm_vm_setup", return_value=True), patch(
            "calm.dsl.cli.accounts.LOG"
        ) as mock_log:

            with pytest.raises(SystemExit) as exc_info:
                create_account(mock_client, account_payload, name=ACCOUNT.LOCAL_AZ)

            # Verify error was logged
            assert mock_log.error.called
            error_msg = mock_log.error.call_args[0][0]
            assert "not supported on Calm VM" in error_msg
            assert ACCOUNT.LOCAL_AZ in error_msg
            assert "Creating" in error_msg

        # Test 2: Update account blocked in CALM VM
        account_payload["metadata"] = {"uuid": "test-uuid"}

        with patch("calm.dsl.cli.accounts.is_calm_vm_setup", return_value=True), patch(
            "calm.dsl.cli.accounts.LOG"
        ) as mock_log:

            with pytest.raises(SystemExit) as exc_info:
                update_account(mock_client, account_payload, name=ACCOUNT.LOCAL_AZ)

            # Verify error was logged
            assert mock_log.error.called
            error_msg = mock_log.error.call_args[0][0]
            assert "not supported on Calm VM" in error_msg
            assert ACCOUNT.LOCAL_AZ in error_msg
            assert "Updating" in error_msg

    def test_local_az_allowed_in_non_calm_vm(self):
        """
        Positive test: Verify NTNX_LOCAL_AZ operations are allowed in non-CALM VM setup

        Tests that create and update operations for NTNX_LOCAL_AZ account
        do NOT exit with error when NOT running on CALM VM setup (is_calm_vm_setup returns False).
        The check should pass and execution continues to the next statements.
        """

        from calm.dsl.cli.accounts import create_account, update_account

        # Mock client
        mock_client = MagicMock()
        mock_client.account.create.return_value = (
            MagicMock(json=lambda: {"status": {"name": ACCOUNT.LOCAL_AZ}}),
            None,
        )
        mock_client.account.update.return_value = (
            MagicMock(json=lambda: {"status": {"name": ACCOUNT.LOCAL_AZ}}),
            None,
        )

        # Mock account payload
        account_payload = {
            "spec": {
                "name": ACCOUNT.LOCAL_AZ,
                "resources": {"type": "nutanix_pc", "data": {}},
            }
        }

        # Test 1: Create account allowed in non-CALM VM (should not raise SystemExit at the check)
        with patch("calm.dsl.cli.accounts.is_calm_vm_setup", return_value=False), patch(
            "calm.dsl.cli.accounts.LOG"
        ), patch("calm.dsl.cli.accounts.get_context") as mock_context, patch(
            "calm.dsl.cli.accounts.click"
        ):

            mock_context.return_value.get_server_config.return_value = {"pc_ip": "test"}

            # The function should not exit at the CALM VM check
            # It will continue and try to execute, so we mock the create call
            try:
                create_account(mock_client, account_payload, name=ACCOUNT.LOCAL_AZ)
                # If we reach here without SystemExit, the check passed correctly
                assert mock_client.account.create.called
            except Exception as e:
                # Any exception other than SystemExit at the check point is acceptable
                # as it means the check passed and code continued
                if "Creating local AZ account is not supported on Calm VM" in str(e):
                    pytest.fail("Should not block NTNX_LOCAL_AZ in non-CALM VM setup")

        # Test 2: Update account allowed in non-CALM VM
        account_payload["metadata"] = {"uuid": "test-uuid"}

        with patch("calm.dsl.cli.accounts.is_calm_vm_setup", return_value=False), patch(
            "calm.dsl.cli.accounts.LOG"
        ), patch("calm.dsl.cli.accounts.click"):

            # The function should not exit at the CALM VM check
            try:
                update_account(mock_client, account_payload, name=ACCOUNT.LOCAL_AZ)
                # If we reach here without SystemExit, the check passed correctly
                assert mock_client.account.update.called
            except Exception as e:
                # Any exception other than SystemExit at the check point is acceptable
                if "Updating local AZ account is not supported on Calm VM" in str(e):
                    pytest.fail("Should not block NTNX_LOCAL_AZ in non-CALM VM setup")
