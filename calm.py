"""Calm CLI

Usage:
  calm.py get blueprints [<name> ...]
  calm.py describe blueprint <name> [--json|--yaml]
  calm.py upload blueprint <name>
  calm.py launch blueprint <name>
  calm.py config [--server <ip:port>] [--username <username>] [--password <password>]
  calm.py (-h | --help)
  calm.py (-v | --version)

Options:
  -h --help                  Show this screen.
  -v --version               Show version.
  -s --server url            Prism Central URL in <ip:port> format
  -u --username username     Prism Central username
  -p --password password     Prism Central password
"""
import json
import warnings
from functools import reduce
from docopt import docopt
from utils import get_api_client, ping

# These will be read from a config file, in the coming days
PC_IP = "10.51.152.102"
PC_PORT = 9440
PC_USERNAME = "admin"
PC_PASSWORD = "***REMOVED***"


def main():
    global PC_IP, PC_PORT, PC_USERNAME, PC_PASSWORD
    names = []

    arguments = docopt(__doc__, version='Calm CLI v0.1.0')
    print(arguments)

    if arguments['config']:
        if arguments['--server']:
            [PC_IP, PC_PORT] = arguments['--server'].split(':')
        if arguments['--username']:
            PC_USERNAME = arguments['--username']
        if arguments['--password']:
            PC_PASSWORD = arguments['--password']

    if arguments['get']:
        names = arguments['<name>']
        get_blueprint_list(names)


def get_blueprint_list(names):
    assert ping() is True
    client = get_api_client()

    params = {
        "length": 20,
        "offset": 0,
    }
    if names:
        search_strings = ['name==.*' + reduce(lambda acc, c: "{}[{}|{}]".
                          format(acc, c.lower(), c.upper()), name, '') + '.*' for name in names
                          ]
        params['filter'] = ''.join(search_strings)

    res, err = client.list(params=params)

    if not err:
        print(">> Blueprint List >>")
        print(json.dumps(res.json(), indent=4, separators=(",", ": ")))
        assert res.ok is True
    else:
        warnings.warn(UserWarning("Cannot fetch blueprints from {}".format(PC_IP)))


if __name__ == "__main__":
    main()
