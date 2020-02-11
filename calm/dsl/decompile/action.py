from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.task import render_task_template
from calm.dsl.builtins import action, CalmTask, ActionType, Service


def render_action_template(cls):

    if not isinstance(cls, ActionType):
        raise TypeError("{} is not of type {}".format(cls, action))

    user_attrs = cls.get_user_attrs()
    runbook = cls.runbook

    main_task = runbook.main_task_local_reference.name
    tasks = []
    for task in runbook.tasks:
        if main_task != task.__name__:
            tasks.append(render_task_template(task))

    data = {
        "name": cls.__name__,
        "description": cls.description or "Sample description",
        "tasks": tasks,
    }
    text = render_template(schema_file="action.py.jinja2", obj=data)
    return text.strip()


class SampleService(Service):
    @action
    def test_action():
        "sample description"
        CalmTask.Exec.ssh(name="Task2", script='echo "Hello"')
        CalmTask.Exec.ssh(name="Task3", script='echo "Hello again"')


print(render_action_template(SampleService.test_action))
