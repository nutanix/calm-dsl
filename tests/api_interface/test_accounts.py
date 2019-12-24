import pytest
import json

from calm.dsl.cli.main import get_api_client


class TestAccounts:
    def test_account_list(self):

        client = get_api_client()
        params = {"length": 20, "offset": 0}
        res, err = client.account.list(params=params)

        if not err:
            print("\n>> Account list call successful>>")
            print(json.dumps(res.json(), indent=4, separators=(",", ": ")))
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
        res, err = client.account.read(account_id)
        if not err:
            print(">> Account read successful >>")
            assert res.ok is True
        else:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
