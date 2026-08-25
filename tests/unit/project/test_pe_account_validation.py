"""
Unit tests for Nutanix PE account validation in project operations.

These tests verify that Nutanix PE accounts (clusters) are properly blocked
from being added to projects through various flows.

**Test Coverage:**

1. **CLI Update with --add_account flag**
   - `test_pe_account_blocked_in_cli_update`: PE accounts should be rejected
   - `test_pc_account_allowed_in_cli_update`: PC accounts should be accepted

2. **Project Update in Append Mode**
   - `test_pe_account_blocked_in_append_mode`: PE accounts should be rejected when merging old payload
   - `test_pc_account_allowed_in_append_mode`: PC accounts should be accepted when merging

3. **DSL Project Compilation**
   - `test_pe_account_blocked_in_dsl_compile`: PE accounts should be rejected during compile
"""

import pytest
from unittest.mock import patch, MagicMock

from calm.dsl.constants import ACCOUNT
from calm.dsl.cli.projects import (
    update_project_using_cli_switches,
    update_payload_from_old_project_data,
)
from calm.dsl.builtins.models.project import ProjectType


class TestPEAccountValidation:
    """Test class for PE account validation in project operations"""

    @pytest.fixture
    def mock_cache_pe_account(self):
        """Fixture that returns PE account data"""
        return {
            "name": "PE_CLUSTER_1",
            "uuid": "pe-account-uuid-123",
            "provider_type": ACCOUNT.PE_ACCOUNT_TYPE,  # "nutanix"
        }

    @pytest.fixture
    def mock_cache_pc_account(self):
        """Fixture that returns PC account data"""
        return {
            "name": "NTNX_LOCAL_AZ",
            "uuid": "pc-account-uuid-456",
            "provider_type": "nutanix_pc",
        }

    @pytest.fixture
    def mock_cache_aws_account(self):
        """Fixture that returns AWS account data"""
        return {
            "name": "AWS_ACCOUNT",
            "uuid": "aws-account-uuid-789",
            "provider_type": "aws",
        }

    def test_pe_account_blocked_in_cli_update(self, mock_cache_pe_account):
        """
        Test that PE accounts are blocked when adding via CLI switches
        Flow: calm update project <name> --add_account <pe_account>
        """
        with patch("calm.dsl.cli.projects.Cache") as mock_cache, patch(
            "calm.dsl.cli.projects.get_api_client"
        ), patch("calm.dsl.cli.projects.LOG") as mock_log:

            # Setup mock to return PE account
            mock_cache.get_entity_data.return_value = mock_cache_pe_account

            # Mock other required objects
            mock_client = MagicMock()
            mock_client.project.get_name_uuid_map.return_value = {
                "test_project": "project-uuid"
            }
            mock_client.project.read.return_value = (
                MagicMock(
                    json=lambda: {
                        "metadata": {"uuid": "project-uuid"},
                        "spec": {
                            "resources": {
                                "user_reference_list": [],
                                "external_user_group_reference_list": [],
                                "account_reference_list": [],
                            }
                        },
                    }
                ),
                None,
            )

            with patch(
                "calm.dsl.cli.projects.get_api_client", return_value=mock_client
            ):
                # Should exit with error when trying to add PE account
                with pytest.raises(SystemExit) as exc_info:
                    update_project_using_cli_switches(
                        project_name="test_project",
                        add_user_list=[],
                        add_group_list=[],
                        add_account_list=["PE_CLUSTER_1"],
                        remove_account_list=[],
                        remove_user_list=[],
                        remove_group_list=[],
                        disable_quotas=False,
                        enable_quotas=False,
                    )

                # Verify error was logged
                assert mock_log.error.called
                error_msg = mock_log.error.call_args[0][0]
                assert "Nutanix PE account" in error_msg
                assert "not supposed to be added" in error_msg

    def test_pc_account_allowed_in_cli_update(self, mock_cache_pc_account):
        """
        Test that PC accounts are allowed when adding via CLI switches
        Flow: calm update project <name> --add_account <pc_account>
        """
        with patch("calm.dsl.cli.projects.Cache") as mock_cache, patch(
            "calm.dsl.cli.projects.get_api_client"
        ) as mock_get_client, patch("calm.dsl.cli.projects.LOG"):

            # Setup mock to return PC account
            mock_cache.get_entity_data.return_value = mock_cache_pc_account

            # Mock client and project data
            mock_client = MagicMock()
            mock_client.project.get_name_uuid_map.return_value = {
                "test_project": "project-uuid"
            }
            mock_client.project.read.return_value = (
                MagicMock(
                    json=lambda: {
                        "metadata": {"uuid": "project-uuid"},
                        "spec": {
                            "resources": {
                                "user_reference_list": [],
                                "external_user_group_reference_list": [],
                                "account_reference_list": [],
                            }
                        },
                    }
                ),
                None,
            )
            mock_client.user.get_name_uuid_map.return_value = {}
            mock_client.user_group.get_name_uuid_map.return_value = {}
            mock_client.project.usage.return_value = (
                MagicMock(
                    json=lambda: {
                        "status": {
                            "resources": {
                                "account_list": [],
                                "subnet_list": [],
                                "cluster_list": [],
                                "vpc_list": [],
                            }
                        }
                    }
                ),
                None,
            )
            mock_client.project.update.return_value = (
                MagicMock(
                    json=lambda: {
                        "metadata": {"uuid": "project-uuid"},
                        "spec": {"name": "test_project"},
                        "status": {
                            "execution_context": {"task_uuid": "task-uuid"},
                        },
                    }
                ),
                None,
            )
            mock_get_client.return_value = mock_client

            with patch(
                "calm.dsl.cli.projects.watch_project_task", return_value="success"
            ), patch("calm.dsl.cli.projects.Cache.update_one"):

                # Should not raise exception for PC account
                try:
                    update_project_using_cli_switches(
                        project_name="test_project",
                        add_user_list=[],
                        add_group_list=[],
                        add_account_list=["NTNX_LOCAL_AZ"],
                        remove_account_list=[],
                        remove_user_list=[],
                        remove_group_list=[],
                        disable_quotas=False,
                        enable_quotas=False,
                    )
                    # If we get here, the PC account was accepted
                    assert True
                except SystemExit:
                    pytest.fail("PC account should be allowed but was blocked")

    def test_pe_account_blocked_in_append_mode(self, mock_cache_pe_account):
        """
        Test that PE accounts are blocked in append-only update mode
        Flow: calm update project <name> -f <file> --append-only
        """
        with patch("calm.dsl.cli.projects.Cache") as mock_cache, patch(
            "calm.dsl.cli.projects.LOG"
        ) as mock_log:

            # Setup mock to return PE account when queried by UUID
            mock_cache.get_entity_data_using_uuid.return_value = mock_cache_pe_account

            # Create mock payloads
            project_payload = {
                "spec": {
                    "resources": {
                        "user_reference_list": [],
                        "external_user_group_reference_list": [],
                        "subnet_reference_list": [],
                        "external_network_list": [],
                        "account_reference_list": [],
                        "vpc_reference_list": [],
                        "cluster_reference_list": [],
                    }
                }
            }

            old_project_payload = {
                "spec": {
                    "resources": {
                        "user_reference_list": [],
                        "external_user_group_reference_list": [],
                        "subnet_reference_list": [],
                        "external_network_list": [],
                        "account_reference_list": [
                            {
                                "uuid": "pe-account-uuid-123",
                                "name": "PE_CLUSTER_1",
                            }
                        ],
                        "vpc_reference_list": [],
                        "cluster_reference_list": [],
                    }
                }
            }

            # Should exit with error when trying to append PE account
            with pytest.raises(SystemExit) as exc_info:
                update_payload_from_old_project_data(
                    project_payload, old_project_payload
                )

            # Verify error was logged
            assert mock_log.error.called
            error_msg = mock_log.error.call_args[0][0]
            assert "Nutanix PE account" in error_msg
            assert "not supposed to be added" in error_msg

    def test_pc_account_allowed_in_append_mode(self, mock_cache_pc_account):
        """
        Test that PC accounts are allowed in append-only update mode
        """
        with patch("calm.dsl.cli.projects.Cache") as mock_cache:

            # Setup mock to return PC account when queried by UUID
            mock_cache.get_entity_data_using_uuid.return_value = mock_cache_pc_account

            # Create mock payloads
            project_payload = {
                "spec": {
                    "resources": {
                        "user_reference_list": [],
                        "external_user_group_reference_list": [],
                        "subnet_reference_list": [],
                        "external_network_list": [],
                        "account_reference_list": [],
                        "vpc_reference_list": [],
                        "cluster_reference_list": [],
                    }
                }
            }

            old_project_payload = {
                "spec": {
                    "resources": {
                        "user_reference_list": [],
                        "external_user_group_reference_list": [],
                        "subnet_reference_list": [],
                        "external_network_list": [],
                        "account_reference_list": [
                            {
                                "uuid": "pc-account-uuid-456",
                                "name": "NTNX_LOCAL_AZ",
                            }
                        ],
                        "vpc_reference_list": [],
                        "cluster_reference_list": [],
                    }
                }
            }

            # Should not raise exception for PC account
            try:
                update_payload_from_old_project_data(
                    project_payload, old_project_payload
                )
                # Verify PC account was added
                assert (
                    len(project_payload["spec"]["resources"]["account_reference_list"])
                    == 1
                )
                assert (
                    project_payload["spec"]["resources"]["account_reference_list"][0][
                        "uuid"
                    ]
                    == "pc-account-uuid-456"
                )
            except SystemExit:
                pytest.fail("PC account should be allowed but was blocked")

    def test_pe_account_blocked_in_dsl_compile(self, mock_cache_pe_account):
        """
        Test that PE accounts are blocked during DSL project compilation
        Flow: calm create/update project with DSL file
        """
        with patch("calm.dsl.builtins.models.project.Cache") as mock_cache, patch(
            "calm.dsl.builtins.models.project.LOG"
        ) as mock_log, patch("calm.dsl.builtins.models.project.get_provider"), patch(
            "calm.dsl.store.version.Version.get_version", return_value="3.5.0"
        ):

            # Setup mock to return PE account
            mock_cache.get_entity_data_using_uuid.return_value = mock_cache_pe_account

            # Create a mock provider with PE account
            mock_provider = MagicMock()
            mock_provider.type = "nutanix_pc"
            mock_provider.get_dict.return_value = {
                "type": "nutanix_pc",
                "account_reference": {
                    "uuid": "pe-account-uuid-123",
                    "name": "PE_CLUSTER_1",
                },
                "subnet_reference_list": [],
                "external_network_list": [],
                "cluster_reference_list": [],
                "vpc_reference_list": [],
            }

            # Create a mock project class
            mock_project_cls = MagicMock(spec=ProjectType)
            mock_project_cls.__bases__ = (object,)
            mock_project_cls.get_dict.return_value = {
                "provider_list": [mock_provider],
                "name": "test_project",
                "description": "test",
            }

            # Mock the super().compile() call
            with patch.object(
                ProjectType.__bases__[0],
                "compile",
                return_value={
                    "provider_list": [mock_provider],
                    "name": "test_project",
                    "description": "test",
                },
            ):
                # Should exit with error when compiling with PE account
                with pytest.raises(SystemExit):
                    ProjectType.compile(mock_project_cls)

                # Verify error was logged
                assert mock_log.error.called
                error_msg = mock_log.error.call_args[0][0]
                assert "Nutanix PE account" in error_msg
                assert "not supposed to be added" in error_msg
