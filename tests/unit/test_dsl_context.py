from calm.dsl.config import get_context


def test_stratos_config():
    ContextObj = get_context()
    stratos_config = ContextObj.get_stratos_config()
    assert stratos_config.get("stratos_status", False) in [True, False]


def test_connection_config():
    ContextObj = get_context()
    connection_config = ContextObj.get_connection_config()
    assert isinstance(connection_config["retries_enabled"], bool)
    assert isinstance(connection_config["connection_timeout"], int)
    assert isinstance(connection_config["read_timeout"], int)
