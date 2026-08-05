from unittest import mock

from calm.dsl.store.version import Version


@mock.patch("calm.dsl.store.version.is_nc_enabled_by_config")
@mock.patch("calm.dsl.store.version.get_context")
@mock.patch("calm.dsl.store.version.get_api_client")
@mock.patch("calm.dsl.store.version.get_db_handle")
def test_version_sync__skips_pc_version_for_nc_enabled_setup(
    get_db_handle_mock,
    get_api_client_mock,
    get_context_mock,
    is_nc_enabled_mock,
):
    """PC version should NOT be fetched or stored when NC is enabled (cloud/NC setup)."""

    is_nc_enabled_mock.return_value = True

    pc_ip = "10.0.0.1"
    get_context_mock.return_value.get_server_config.return_value = {"pc_ip": pc_ip}

    calm_version_response = mock.MagicMock()
    calm_version_response.content = b"4.5.0"
    get_api_client_mock.return_value.version.get_calm_version.return_value = (
        calm_version_response,
        None,
    )

    db_mock = get_db_handle_mock.return_value

    Version.sync()

    # Calm version must always be created
    db_mock.version_table.create.assert_called_once_with(
        name="Calm", pc_ip=pc_ip, version="4.5.0"
    )

    # PC version API must NOT be called for NC-enabled setups
    get_api_client_mock.return_value.version.get_pc_version.assert_not_called()


@mock.patch("calm.dsl.store.version.is_nc_enabled_by_config")
@mock.patch("calm.dsl.store.version.get_context")
@mock.patch("calm.dsl.store.version.get_api_client")
@mock.patch("calm.dsl.store.version.get_db_handle")
def test_version_sync__fetches_pc_version_for_onprem_setup(
    get_db_handle_mock,
    get_api_client_mock,
    get_context_mock,
    is_nc_enabled_mock,
):
    """PC version SHOULD be fetched and stored for on-prem (non-NC) setups."""

    is_nc_enabled_mock.return_value = False

    pc_ip = "10.0.0.1"
    pc_version = "master"
    get_context_mock.return_value.get_server_config.return_value = {"pc_ip": pc_ip}

    calm_version_response = mock.MagicMock()
    calm_version_response.content = b"4.5.0"

    pc_version_response = mock.MagicMock()
    pc_version_response.json.return_value = {"version": pc_version}

    client_mock = get_api_client_mock.return_value
    client_mock.version.get_calm_version.return_value = (calm_version_response, None)
    client_mock.version.get_pc_version.return_value = (pc_version_response, None)

    db_mock = get_db_handle_mock.return_value

    Version.sync()

    # Both Calm and PC versions must be created for on-prem
    assert db_mock.version_table.create.call_count == 2
    db_mock.version_table.create.assert_any_call(
        name="Calm", pc_ip=pc_ip, version="4.5.0"
    )
    db_mock.version_table.create.assert_any_call(
        name="PC", pc_ip=pc_ip, version=pc_version
    )
