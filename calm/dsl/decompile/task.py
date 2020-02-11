from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import TaskType, CalmTask

# In service and package helper make sure that targer is erased


def render_task_template(cls):

    if not isinstance(cls, TaskType):
        raise TypeError("{} is not of type {}".format(cls, TaskType))

    user_attrs = cls.get_user_attrs()
    macro_name = ""

    # sample for exec and ssh type task
    if cls.type == "EXEC":
        script_type = cls.attrs["script_type"]
        cls.attrs["script"] = cls.attrs["script"].replace("'", r"/'")
        if script_type == "sh":
            schema_file = "task_exec_ssh.py.jinja2"

        elif script_type == "escript":
            schema_file = "task_exec_escript.py.jinja2"

        elif script_type == "npsscript":
            schema_file = "task_exec_powershell.py.jinja2"

    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()


task1 = CalmTask.Exec.ssh(name="Task1", script="echo @@{foo}@@")
# print(render_task_template(task1))
