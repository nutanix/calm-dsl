import click
from functools import reduce


def get_states_filter(STATES_CLASS, state_key="state"):

    states = []
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
        return ",".join(search_strings)


def highlight_text(text, **kwargs):
    """Highlight text in our standard format"""
    return click.style("{}".format(text), fg="blue", bold=False, **kwargs)
