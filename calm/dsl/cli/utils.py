import click
import importlib.util
from functools import reduce
from asciimatics.screen import Screen


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


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)


def get_module_from_file(module_name, file):
    """Returns a module given a user python file (.py)"""

    spec = importlib.util.spec_from_file_location(module_name, file)
    user_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_module)

    return user_module


def import_var_from_file(file, var, default_value=None):
    try:
        module = get_module_from_file(var, file)
        return getattr(module, var)
    except:     # NoQA
        return default_value


class Display:
    @classmethod
    def wrapper(cls, func, watch=False):
        if watch:
            Screen.wrapper(func)
        else:
            func(display)

    def clear(self):
        pass

    def refresh(self):
        pass

    def wait_for_input(self, *args):
        pass

    def print_at(self, text, x, *args):
        click.echo("{}{}".format((" " * x), text))


display = Display()
