from unittest import mock

from calm.dsl.api.connection import Connection
from calm.dsl.api.util import is_ncm_enabled


@mock.patch("calm.dsl.api.util.get_resource_api")
def test_is_ncm_enabled_returns_false_on_create_error(get_resource_api_mock):
    """
    When dm/v3/groups create fails, is_ncm_enabled must return (False, None)
    and must not raise on a None response.
    """
    client = mock.Mock()
    client.connection = Connection(host="pc.example", port=9440)

    resource_api = mock.Mock()
    resource_api.create.return_value = (
        None,
        {"code": 503, "error": "Connection refused"},
    )
    get_resource_api_mock.return_value = resource_api

    result = is_ncm_enabled(client)

    assert result == (False, None)
    resource_api.create.assert_called_once()
