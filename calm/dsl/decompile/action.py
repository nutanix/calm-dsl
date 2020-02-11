from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.task import render_task_template
from calm.dsl.decompile.variable import render_variable_template
from calm.dsl.builtins import action, CalmTask, ActionType, Service, CalmVariable, ServiceType


def render_action_template(cls):

    if not isinstance(cls, ActionType):
        raise TypeError("{} is not of type {}".format(cls, action))

    user_attrs = cls.get_user_attrs()
    runbook = cls.runbook

    main_task = runbook.main_task_local_reference.__name__
    tasks = []
    for task in runbook.tasks:
        if main_task != task.__name__:
            tasks.append(render_task_template(task))
    
    variables = []
    for variable in runbook.variables:
        variables.append(render_variable_template(variable))
    
    data = {
        "name": cls.__name__,
        "description": cls.description or "Sample description",
        "tasks": tasks,
        "variables": variables
    }
    text = render_template(schema_file="action.py.jinja2", obj=data)
    return text.strip()


class SampleService(Service):
    @action
    def test_action():
        "sample description"
        var1 = CalmVariable.Simple(  # noqa
            "var1_val",
            label="var1_label",
            regex="^[a-zA-Z0-9_]+$",
            validate_regex=True,
            runtime=True,
        )
        var2 = CalmVariable.Simple.Secret(  # noqa
            "var2_val",
            label="var2_label",
            regex="^[a-zA-Z0-9_]+$",
            validate_regex=True,
            is_hidden=True,
            is_mandatory=True,
        )
        CalmTask.Exec.ssh(name="Task2", script='echo "Hello"')
        CalmTask.Exec.ssh(name="Task3", script='echo "Hello again"')

data = SampleService.get_dict()
service_class = ServiceType.decompile(data)


print(render_action_template(service_class.actions[0]))
