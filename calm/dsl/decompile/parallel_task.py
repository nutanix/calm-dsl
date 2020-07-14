from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.task import render_task_template


def render_parallel_task_template(task_list, entity_context, RUNBOOK_ACTION_MAP):
    """render parallel tasks template"""

    rendered_tasks = []
    for task in task_list:
        rendered_tasks.append(
            render_task_template(task, entity_context, RUNBOOK_ACTION_MAP)
        )

    user_attrs = {"tasks": rendered_tasks}

    text = render_template(schema_file="parallel_task.py.jinja2", obj=user_attrs)
    return text.strip()
