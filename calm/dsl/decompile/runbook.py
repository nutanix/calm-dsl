import uuid
from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.metadata import render_metadata_template
from calm.dsl.decompile.task_tree import render_task_tree_template
from calm.dsl.decompile.variable import (
    render_variable_template,
    get_secret_variable_files,
)
from calm.dsl.decompile.endpoint import render_endpoint
from calm.dsl.decompile.credential import (
    render_credential_template,
    get_cred_files,
    get_cred_var_name,
)
from calm.dsl.decompile.decompile_helpers import process_variable_name
from calm.dsl.builtins import CalmEndpoint as Endpoint
from calm.dsl.builtins.models.runbook import RunbookType, runbook
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)
RUNBOOK_ACTION_MAP = {}


def render_runbook_template(
    runbook_cls,
    metadata_obj=None,
    entity_context="",
    CONFIG_SPEC_MAP={},
    credentials=[],
    default_endpoint=None,
):
    global RUNBOOK_ACTION_MAP
    LOG.debug("Rendering {} runbook template".format(runbook_cls.__name__))
    if not isinstance(runbook_cls, RunbookType):
        raise TypeError("{} is not of type {}".format(runbook_cls, runbook))
    # Update entity context
    entity_context = entity_context + "_Runbook_" + runbook_cls.__name__

    runbook_name = getattr(runbook_cls, "name", "") or runbook_cls.__name__
    # Note cls.__name__ should be used for call_runbook tasks
    RUNBOOK_ACTION_MAP[runbook_name] = runbook_cls.__name__

    # get endpoints and render them
    endpoints = []
    ep_list = []
    for ind, task in enumerate(runbook_cls.tasks):
        ep = task.target_any_local_reference
        if ep:
            if ep.name in ep_list:
                continue
            endpoints.append(render_endpoint(ep))
            ep_list.append(ep.name)
    default_endpoint_name = ""
    if default_endpoint:
        default_endpoint_name = default_endpoint["name"]
        if default_endpoint_name not in ep_list:
            ep_list.append(default_endpoint_name)
            endpoints.append(
                render_endpoint(Endpoint.use_existing(default_endpoint_name))
            )

    default_endpoint_name = process_variable_name(default_endpoint_name)

    rendered_credential_list = []
    credentials_list = []
    for cred in credentials:
        rendered_credential_list.append(render_credential_template(cred))
        credentials_list.append(get_cred_var_name(cred.name))
    # get mapping used for rendering task_tree template

    root_node, task_child_map, decision_tasks, while_loop_tasks = get_task_order(
        runbook_cls.tasks
    )
    tasks = []
    tasks.append(
        render_task_tree_template(
            root_node,
            task_child_map,
            entity_context,
            RUNBOOK_ACTION_MAP,
            CONFIG_SPEC_MAP,
            decision_tasks,
            while_tasks=while_loop_tasks,
        )
    )
    variables = []
    for variable in runbook_cls.variables:
        variables.append(render_variable_template(variable, entity_context))
    secret_files = get_secret_variable_files()
    secret_files.extend(get_cred_files())
    if not (variables or tasks):
        return ""
    import_status = False
    if while_loop_tasks:
        import_status = True

    # runbook project reference
    project_name = metadata_obj.project["name"]
    user_attrs = {
        "name": runbook_cls.__name__,
        "description": runbook_cls.__doc__ or "",
        "secret_files": secret_files,
        "endpoints": endpoints,
        "credentials_list": credentials_list,
        "credentials": rendered_credential_list,
        "tasks": tasks,
        "variables": variables,
        "project_name": project_name,
        "import_status": import_status,
        "default_endpoint_name": default_endpoint_name,
    }

    gui_display_name = getattr(runbook_cls, "name", "") or runbook_cls.__name__
    if gui_display_name != runbook_cls.__name__:
        user_attrs["gui_display_name"] = gui_display_name

    text = render_template(schema_file="runbook.py.jinja2", obj=user_attrs)
    return text.strip()


def get_task_order(task_list):
    """Returns the list where each index represents a list of task that executes parallely"""

    dag_task = None
    for ind, task in enumerate(task_list):
        if task.type == "DAG":
            dag_task = task
            task_list.pop(ind)
            break

    if not dag_task:
        raise ValueError("Dag task not found")

    # Edges between tasks
    edges = dag_task.attrs["edges"]
    # for decision and while_loop tasks, their subtasks are not linked with the main task tree
    # populate the decision tasks.
    # populate the while_loop tasks
    decision_tasks = {}
    decision_child_tasks = []

    def insert_decision_task_node(task):
        failure_meta_task_name = task.attrs["failure_child_reference"]["name"]
        success_meta_task_name = task.attrs["success_child_reference"]["name"]
        failure_meta_task = list(
            filter(lambda x: x.name == failure_meta_task_name, task_list)
        )[0]
        success_meta_task = list(
            filter(lambda x: x.name == success_meta_task_name, task_list)
        )[0]
        parent = task
        if parent.name not in decision_tasks:
            decision_tasks[parent.name] = {"data": parent}
        for child_task in failure_meta_task.child_tasks_local_reference_list:
            if "failure_tasks" not in decision_tasks[parent.name]:
                decision_tasks[parent.name]["failure_tasks"] = []
            real_child_task = list(
                filter(lambda x: x.name == child_task.name, task_list)
            )[0]
            decision_tasks[parent.name]["failure_tasks"].append(
                {"name": child_task.name, "data": real_child_task}
            )
            decision_child_tasks.append(child_task.name)

        for child_task in success_meta_task.child_tasks_local_reference_list:
            if "success_tasks" not in decision_tasks[parent.name]:
                decision_tasks[parent.name]["success_tasks"] = []
            real_child_task = list(
                filter(lambda x: x.name == child_task.name, task_list)
            )[0]
            decision_tasks[parent.name]["success_tasks"].append(
                {"name": child_task.name, "data": real_child_task}
            )
            decision_child_tasks.append(child_task.name)

    while_loop_tasks = {}
    while_loop_child_tasks = []

    def insert_while_loop_tasks(task):
        while_loop_tasks[task.name] = {"data": task, "child_tasks": []}
        child_meta_task_name = task.child_tasks_local_reference_list[0].name
        child_meta_task = list(
            filter(lambda x: x.name == child_meta_task_name, task_list)
        )[0]
        child_tasks = child_meta_task.child_tasks_local_reference_list
        for child_task in child_tasks:
            real_child_task = list(
                filter(lambda x: x.name == child_task.name, task_list)
            )[0]
            while_loop_tasks[task.name]["child_tasks"].append(real_child_task)
            while_loop_child_tasks.append(real_child_task.name)

    for task in task_list:
        if task.type == "DECISION":
            insert_decision_task_node(task)
        elif task.type == "WHILE_LOOP":
            insert_while_loop_tasks(task)

    # remove meta tasks as they are not rendered.
    task_list = list(
        filter(
            lambda x: (
                x.type != "META"
                and (x.name not in (decision_child_tasks + while_loop_child_tasks))
            ),
            task_list,
        )
    )
    # Final resultant task list with level as index
    res_task_list = []

    # map to store the edges from given  task
    task_edges_map = {}

    # map to store indegree of every task
    task_indegree_count_map = {}

    # create task map with name
    task_name_data_map = {}
    for task in task_list:
        task_name = task.name
        task_name_data_map[task_name] = task
        task_indegree_count_map[task_name] = 0
        task_edges_map[task_name] = []

    # store in degree of every task
    for edge in edges:
        from_task = edge["from_task_reference"]
        to_task = edge["to_task_reference"]
        task_indegree_count_map[to_task.name] += 1
        task_edges_map[from_task.name].append(to_task.name)

    # Queue to store elements having indegree 0
    queue = []

    # Push elements having indegree = 0
    for task_name, indegree in task_indegree_count_map.items():
        if indegree == 0:
            queue.append(task_name)

    # Here we are taking the name of root node as random to avoid any conflicts
    root_node = str(uuid.uuid4())
    task_child_map = {}
    q = []

    for task_name in queue:
        if (root_node, 0) not in task_child_map:
            task_child_map[(root_node, 0)] = []
            q.append((root_node, 0))

        task_child_map[(root_node, 0)].append(
            {"task_name": task_name, "task_data": task_name_data_map[task_name]}
        )

    while q:
        n = len(q)

        while n:
            task_key = q.pop(0)
            for task in task_child_map[task_key]:
                for child in task_edges_map[task.get("task_name")]:
                    child_task_key = (task.get("task_name"), (task_key[1] + 1))
                    if child_task_key not in task_child_map:
                        task_child_map[child_task_key] = []
                        q.append(child_task_key)

                    task_child_map[child_task_key].append(
                        {"task_name": child, "task_data": task_name_data_map[child]}
                    )

            n -= 1

    return root_node, task_child_map, decision_tasks, while_loop_tasks


def init_action_globals():

    global RUNBOOK_ACTION_MAP
    RUNBOOK_ACTION_MAP = {}


# Used for registering service action runbook earlier before parsing that template
def update_runbook_action_map(runbook_name, action_name):

    global RUNBOOK_ACTION_MAP
    RUNBOOK_ACTION_MAP[runbook_name] = action_name
