from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.task import render_task_template
from calm.dsl.decompile.variable import render_variable_template
from calm.dsl.builtins import action, ActionType


RUNBOOK_ACTION_MAP = {}


def render_action_template(cls):

    global RUNBOOK_REF_MAP
    if not isinstance(cls, ActionType):
        raise TypeError("{} is not of type {}".format(cls, action))

    runbook = cls.runbook
    RUNBOOK_ACTION_MAP[runbook.__name__] = cls.__name__
    tasks = []
    for task in runbook.tasks:
        if task.type != "DAG":
            tasks.append(render_task_template(task, RUNBOOK_ACTION_MAP))

    variables = []
    for variable in runbook.variables:
        variables.append(render_variable_template(variable))

    user_attrs = {
        "name": cls.__name__,
        "description": cls.description or "Sample description",
        "tasks": tasks,
        "variables": variables,
    }
    text = render_template(schema_file="action.py.jinja2", obj=user_attrs)
    return text.strip()
