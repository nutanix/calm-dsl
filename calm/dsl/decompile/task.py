from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.ref import render_ref_template
from calm.dsl.builtins import TaskType, CalmTask, Service, ref
from calm.dsl.builtins import basic_cred

# In service and package helper make sure that targer is erased


def render_task_template(cls):

    if not isinstance(cls, TaskType):
        raise TypeError("{} is not of type {}".format(cls, TaskType))

    user_attrs = cls.get_user_attrs()
    macro_name = ""

    # sample for exec and ssh type task

    target = getattr(cls, "target_any_local_reference", None)
    if target:
        user_attrs["target"] = render_ref_template(target)

    cred = cls.attrs.get("login_credential_local_reference", None)
    if cred:
        user_attrs["cred"] = render_ref_template(cred)

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


class SampleService(Service):
    pass

DefaultCred = basic_cred("user", "pass", "default_cre")



task1 = CalmTask.Exec.ssh(name="Task1", script="echo @@{foo}@@" )
task2 = CalmTask.Exec.ssh(name="Task2", script="echo @@{foo}@@", cred=ref(DefaultCred))
task3 = CalmTask.Exec.ssh(name="Task3", script="echo @@{foo}@@", target=ref(SampleService))
task4 = CalmTask.Exec.ssh(name="Task4", script="echo @@{foo}@@", target=ref(SampleService), cred=ref(DefaultCred))
# print(render_task_template(task4))
