import uuid
import click
import sys
import os
from functools import reduce
from asciimatics.screen import Screen
from click_didyoumean import DYMMixin
from distutils.version import LooseVersion as LV

from calm.dsl.tools import get_module_from_file
from calm.dsl.api import get_api_client
from calm.dsl.constants import PROVIDER_ACCOUNT_TYPE_MAP
from calm.dsl.store import Version
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def get_states_filter(STATES_CLASS=None, state_key="state", states=[]):

    if not states:
        for field in vars(STATES_CLASS):
            if not field.startswith("__"):
                states.append(getattr(STATES_CLASS, field))
    state_prefix = ",{}==".format(state_key)
    return ";({}=={})".format(state_key, state_prefix.join(states))


def get_name_query(names):
    if names:
        search_strings = [
            "name==.*"
            + reduce(
                lambda acc, c: "{}[{}|{}]".format(acc, c.lower(), c.upper()), name, ""
            )
            + ".*"
            for name in names
        ]
        return "({})".format(",".join(search_strings))
    return ""


def _get_nested_messages(path, obj, message_list):
    """Get nested message list objects from the blueprint"""
    if isinstance(obj, list):
        for _, sub_obj in enumerate(obj):
            _get_nested_messages(path, sub_obj, message_list)
    elif isinstance(obj, dict):
        name = obj.get("name", "")
        if name and isinstance(name, str):
            path = path + ("." if path else "") + name
        for key in obj:
            sub_obj = obj[key]
            if key == "message_list":
                for message in sub_obj:
                    message["path"] = path
                    message_list.append(message)
                continue
            _get_nested_messages(path, sub_obj, message_list)


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)


def import_var_from_file(file, var, default_value=None):
    try:
        module = get_module_from_file(var, file)
        return getattr(module, var)
    except:  # NoQA
        return default_value


class Display:
    @classmethod
    def wrapper(cls, func, watch=False):
        if watch and os.isatty(sys.stdout.fileno()):
            Screen.wrapper(func, height=1000)
        else:
            func(display)

    def clear(self):
        pass

    def refresh(self):
        pass

    def wait_for_input(self, *args):
        pass

    def print_at(self, text, x, *args, **kwargs):
        click.echo("{}{}".format((" " * x), text))


display = Display()


class FeatureFlagMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_version_map = dict()
        self.experimental_cmd_map = dict()

    def command(self, *args, **kwargs):
        """Behaves the same as `click.Group.command()` except added an
        `feature_min_version` flag which can be used to warn users if command
        is not supported setup calm version.
        """

        feature_min_version = kwargs.pop("feature_min_version", None)
        if feature_min_version and args:
            self.feature_version_map[args[0]] = feature_min_version

        is_experimental = kwargs.pop("experimental", False)
        if args:
            self.experimental_cmd_map[args[0]] = is_experimental

        return super().command(*args, **kwargs)

    def invoke(self, ctx):

        if not ctx.protected_args:
            return super(FeatureFlagMixin, self).invoke(ctx)

        cmd_name = ctx.protected_args[0]

        feature_min_version = self.feature_version_map.get(cmd_name, "")
        if feature_min_version:
            calm_version = Version.get_version("Calm")
            if not calm_version:
                LOG.error("Calm version not found. Please update cache")
                sys.exit(-1)

            if LV(calm_version) >= LV(feature_min_version):
                return super().invoke(ctx)

            else:
                LOG.warning(
                    "Please update Calm (v{} -> >=v{}) to use this command.".format(
                        calm_version, feature_min_version
                    )
                )
                return None

        else:
            return super().invoke(ctx)


class FeatureFlagGroup(FeatureFlagMixin, DYMMixin, click.Group):
    """click Group that have *did-you-mean* functionality and adds *feature_min_version* paramter to each subcommand
    which can be used to set minimum calm version for command"""

    pass


class FeatureDslOption(click.ParamType):

    name = "feature-dsl-option"

    def __init__(self, feature_min_version=""):
        self.feature_min_version = feature_min_version

    def convert(self, value, param, ctx):

        if self.feature_min_version:
            calm_version = Version.get_version("Calm")
            if not calm_version:
                LOG.error("Calm version not found. Please update cache")
                sys.exit(-1)

            # TODO add the pc version to warning also
            if LV(calm_version) < LV(self.feature_min_version):
                LOG.error(
                    "Calm {} does not support '{}' option. Please upgrade server to Calm {}".format(
                        calm_version, param.name, self.feature_min_version
                    )
                )
                sys.exit(-1)

        # Add validation for file types etc.
        return value


def get_account_details(
    project_name, account_name, provider_type="AHV_VM", pe_account_needed=False
):
    """returns object containing project and account details"""

    client = get_api_client()

    # Getting the account uuid map
    account_type = PROVIDER_ACCOUNT_TYPE_MAP[provider_type]
    params = {"length": 250, "filter": "state!=DELETED;type=={}".format(account_type)}
    if account_name:
        params["filter"] += ";name=={}".format(account_name)

    account_uuid_name_map = client.account.get_uuid_name_map(params)
    provider_account_uuids = list(account_uuid_name_map.keys())

    LOG.info("Fetching project '{}' details".format(project_name))
    params = {"length": 250, "filter": "name=={}".format(project_name)}
    res, err = client.project.list(params)
    if err:
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    if res["metadata"]["total_matches"] == 0:
        LOG.error("Project {} not found".format(project_name))
        sys.exit(-1)

    pj_data = res["entities"][0]
    whitelisted_accounts = [
        account["uuid"]
        for account in pj_data["status"]["resources"].get("account_reference_list", [])
    ]

    project_uuid = pj_data["metadata"]["uuid"]
    account_uuid = ""
    for _account_uuid in whitelisted_accounts:
        if _account_uuid in provider_account_uuids:
            account_uuid = _account_uuid
            break

    if not account_uuid:
        LOG.error("No account with given details found in project")
        sys.exit(-1)

    account_name = account_uuid_name_map[account_uuid]

    if pe_account_needed and provider_type == "AHV_VM":
        LOG.info("Fetching account '{}' details".format(account_name))
        res, err = client.account.read(account_uuid)
        if err:
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        clusters = res["status"]["resources"]["data"].get(
            "cluster_account_reference_list", []
        )
        if not clusters:
            LOG.error(
                "No cluster found in ahv account (uuid='{}')".format(account_uuid)
            )
            sys.exit(-1)

        # Use cluster uuid for AHV account
        account_uuid = clusters[0]["uuid"]

    return {
        "project": {"name": project_name, "uuid": project_uuid},
        "account": {"name": account_name, "uuid": account_uuid},
    }


def insert_uuid(action, name_uuid_map, action_list_with_uuid):
    """
    Helper function to insert uuids in action_list
    """

    # if action is of type list then recursively call insert_uuid for each element
    if isinstance(action, list):
        for i in range(len(action)):
            if isinstance(action[i], (dict, list)):
                insert_uuid(action[i], name_uuid_map, action_list_with_uuid[i])
    elif isinstance(action, dict):
        for key, value in action.items():
            # if the key is name then assign a unique uuid to it if not already assigned
            if key == "name":
                if value not in name_uuid_map:
                    name_uuid_map[value] = str(uuid.uuid4())
                # inserting the uuid using name_uuid_map
                action_list_with_uuid["uuid"] = name_uuid_map[value]
            elif isinstance(value, (dict, list)):
                insert_uuid(value, name_uuid_map, action_list_with_uuid[key])
