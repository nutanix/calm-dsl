import pytest

from calm.dsl.cli.main import get_api_client
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class TestAccounts:
    def test_account_list(self):

        client = get_api_client()
        params = {"length": 20, "offset": 0}
        LOG.info("Invoking list api call on accounts")
        res, err = client.account.list(params=params)

        if not err:
            LOG.info("Success")
            LOG.debug("Response: {}".format(res.json()))
            assert res.ok is True
        else:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    def test_account_read(self):

        client = get_api_client()
        params = {"length": 20, "offset": 0}
        res, err = client.account.list(params=params)

        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        entities = res["entities"]

        account_id = entities[0]["metadata"]["uuid"]
        LOG.info("Invoking read api call on account (UUID: {})".format(account_id))
        res, err = client.account.read(account_id)
        if not err:
            LOG.info("Success")
            LOG.debug("Response: {}".format(res.json()))
            assert res.ok is True
        else:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
