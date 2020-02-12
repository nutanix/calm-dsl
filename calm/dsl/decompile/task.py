import json

from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.ref import render_ref_template
from calm.dsl.builtins import TaskType, CalmTask, Service, ref
from calm.dsl.builtins import basic_cred, Package, Deployment, Substrate

# In service and package helper make sure that targer is erased


def render_task_template(cls):

    if not isinstance(cls, TaskType):
        raise TypeError("{} is not of type {}".format(cls, TaskType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
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

        elif script_type == "static":
            schema_file = "task_exec_escript.py.jinja2"

        elif script_type == "npsscript":
            schema_file = "task_exec_powershell.py.jinja2"

    elif cls.type == "SET_VARIABLE":
        variables = cls.attrs.get("eval_variables", None)
        if variables:
            user_attrs["variables"] = variables
        script_type = cls.attrs["script_type"]
        cls.attrs["script"] = cls.attrs["script"].replace("'", r"/'")
        if script_type == "sh":
            schema_file = "task_setvariable_ssh.py.jinja2"

        elif script_type == "static":
            schema_file = "task_setvariable_escript.py.jinja2"

        elif script_type == "npsscript":
            schema_file = "task_setvariable_powershell.py.jinja2"

    elif cls.type == "DELAY":
        delay_seconds = getattr(cls, "interval_secs", None)
        if delay_seconds:
            user_attrs["delay_seconds"] = delay_seconds
        schema_file = "task_delay.py.jinja2"

    elif cls.type == "SCALING":
        scaling_count = cls.attrs.get("scaling_count", 1)
        if scaling_count:
            user_attrs["scaling_count"] = scaling_count
        scaling_type = cls.attrs["scaling_type"]
        if scaling_type == "SCALEOUT":
            schema_file = "task_scaling_scaleout.py.jinja2"

        elif scaling_type == "SCALEIN":
            schema_file = "task_scaling_scalein.py.jinja2"
    elif cls.type == "HTTP":
        attrs = cls.attrs

        auth_obj = attrs["authentication"]

        # TODO modify auth_bj to go to credential class, so setting to None now
        user_attrs["credential"] = None
        user_attrs["headers"] = {}
        user_attrs["secret_headers"] = {}
        user_attrs["status_mapping"] = {}

        for var in attrs.get("headers", []):
            var_type = var.type
            if var.type == "LOCAL":
                user_attrs["headers"][var.name] = var.value

            elif var.type == "SECRET":
                user_attrs["secret_headers"][var.name] = var.value

        for status in attrs.get("expected_response_params", []):
            user_attrs["status_mapping"][status["code"]] = (
                True if status["status"] == "SUCCESS" else False
            )

        user_attrs["response_paths"] = attrs.get("response_paths", {})
        method = attrs["method"]

        if method == "GET":
            schema_file = "task_http_get.py.jinja2"

        elif method == "POST":
            schema_file = "task_http_post.py.jinja2"

        elif method == "PUT":
            schema_file = "task_http_put.py.jinja2"

        elif method == "DELETE":
            schema_file = "task_http_delete.py.jinja2"

    elif cls.type == "CALL_RUNBOOK":
        raise Exception("Not supported")

    else:
        raise Exception("Invalid task type")

    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()


class SampleService(Service):
    pass


class SamplePackage(Package):
    services = [ref(SampleService)]


class SampleSubstrate(Substrate):
    pass


class SampleDeployment(Deployment):
    packages = [ref(SamplePackage)]
    substrate = ref(SampleSubstrate)


DefaultCred = basic_cred("user", "pass", "default_cre")

task1 = CalmTask.Exec.ssh(name="Task1", script="echo @@{foo}@@")
task2 = CalmTask.Exec.ssh(name="Task2", script="echo @@{foo}@@", cred=ref(DefaultCred))
task3 = CalmTask.Exec.ssh(
    name="Task3", script="echo @@{foo}@@", target=ref(SampleService)
)
task4 = CalmTask.Exec.ssh(
    name="Task4",
    script="echo @@{foo}@@",
    target=ref(SampleService),
    cred=ref(DefaultCred),
)
task9 = CalmTask.HTTP.get(
    "https://jsonplaceholder.typicode.com/posts/1",
    credential=DefaultCred,
    headers={"Content-Type": "application/json"},
    secret_headers={"secret_header": "secret"},
    content_type="application/json",
    verify=True,
    status_mapping={200: True},
    response_paths={"foo_title": "$.title"},
    name="Test HTTP Task Get",
    target=ref(SampleService),
)
task10 = CalmTask.HTTP.post(
    "https://jsonplaceholder.typicode.com/posts",
    body=json.dumps({"id": 1, "title": "foo", "body": "bar", "userId": 1}),
    headers={"Content-Type": "application/json"},
    content_type="application/json",
    verify=True,
    status_mapping={200: True},
    response_paths={"foo_title": "$.title"},
    name="Test HTTP Task Post",
    target=ref(SampleService),
)
task11 = CalmTask.HTTP.put(
    "https://jsonplaceholder.typicode.com/posts/1",
    body=json.dumps({"id": 1, "title": "foo", "body": "bar", "userId": 1}),
    headers={"Content-Type": "application/json"},
    content_type="application/json",
    verify=True,
    status_mapping={200: True},
    response_paths={"foo_title": "$.title"},
    name="Test HTTP Task Put",
    target=ref(SampleService),
)
task12 = CalmTask.HTTP.delete(
    "https://jsonplaceholder.typicode.com/posts/1",
    headers={"Content-Type": "application/json"},
    content_type="application/json",
    verify=True,
    status_mapping={200: True},
    name="Test HTTP Task Delete",
    target=ref(SampleService),
)

task5 = CalmTask.Exec.escript(name="Task5", script="echo @@{foo}@@")
task6 = CalmTask.Exec.powershell(
    name="Task5", script="echo @@{foo}@@", cred=ref(DefaultCred)
)
task7 = CalmTask.SetVariable.ssh(
    name="Task5",
    script="print 'var1=test",
    variables=["var1"],
    target=ref(SampleService),
    cred=ref(DefaultCred),
)
delayTask = CalmTask.Delay(delay_seconds=60, target=ref(SampleService))
scaleoutTask = CalmTask.Scaling.scale_out(
    1, target=ref(SampleDeployment), name="Scale out Lamp"
)
scaleinTask = CalmTask.Scaling.scale_in(
    1, target=ref(SampleDeployment), name="Scale in Lamp"
)
# print(render_task_template(task7))
# print(render_task_template(task6))
# print (render_task_template(delayTask))

task_data = task5.get_dict()
task_cls = TaskType.decompile(task_data)
# print (render_task_template(task_cls))
