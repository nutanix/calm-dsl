import click
import sys
import os
from functools import reduce
from asciimatics.screen import Screen
from click_didyoumean import DYMMixin
from distutils.version import LooseVersion as LV

from calm.dsl.log import get_logging_handle
from calm.dsl.tools import get_module_from_file
from calm.dsl.store import Version

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
            Screen.wrapper(func, height=1000, catch_interrupt=True)
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
