import uuid

from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.task import render_task_template
from calm.dsl.decompile.parallel_task import render_parallel_task_template
from calm.dsl.decompile.task_tree import render_task_tree_template
from calm.dsl.decompile.endpoint import render_endpoint
from calm.dsl.decompile.variable import render_variable_template
from calm.dsl.builtins import action, ActionType
from calm.dsl.constants import SUBSTRATE
from calm.dsl.log import get_logging_handle
from calm.dsl.decompile.ref_dependency import get_power_action_substrate_map
from calm.dsl.decompile.decompile_helpers import modify_var_format

LOG = get_logging_handle(__name__)
RUNBOOK_ACTION_MAP = {}


def render_action_template(
    cls,
    entity_context="",
    CONFIG_SPEC_MAP={},
    context="",
    secrets_dict=[],
    endpoints=[],
    ep_list=[],
    credential_list=[],
    rendered_credential_list=[],
):

    global RUNBOOK_ACTION_MAP
    LOG.debug("Rendering {} action template".format(cls.__name__))
    if not isinstance(cls, ActionType):
        raise TypeError("{} is not of type {}".format(cls, action))

    # Update entity context
    # TODO for now, not adding runbook to context as current mapping -is 1:1
    entity_context = entity_context + "_Action_" + cls.__name__
    context = (
        context + "action_list." + (getattr(cls, "name", "") or cls.__name__) + "."
    )

    runbook = cls.runbook
    runbook_name = getattr(runbook, "name", "") or runbook.__name__
    runbook_context = context + "runbook." + runbook_name + "."

    # Note cls.__name__ should be used for call_runbook tasks
    RUNBOOK_ACTION_MAP[runbook_name] = cls.__name__

    # NOTE Not using main_task_local_reference for now,
    # bcz type of main task is "DAG"
    root_node, task_child_map, decision_tasks, while_loop_tasks = get_task_order(
        runbook.tasks
    )

    tasks = []
    if task_child_map:
        tasks.append(
            render_task_tree_template(
                root_node,
                task_child_map,
                entity_context,
                RUNBOOK_ACTION_MAP,
                CONFIG_SPEC_MAP,
                context=runbook_context,
                secrets_dict=secrets_dict,
                decision_tasks=decision_tasks,
                while_tasks=while_loop_tasks,
                credentials_list=credential_list,
                rendered_credential_list=rendered_credential_list,
            )
        )

    variables = []
    for variable in runbook.variables:
        variables.append(
            render_variable_template(
                variable,
                entity_context,
                context=runbook_context,
                secrets_dict=secrets_dict,
                credentials_list=credential_list,
                rendered_credential_list=rendered_credential_list,
                endpoints=endpoints,
                ep_list=ep_list,
            )
        )

    # not returning vm power actions, even if they don't have tasks, to include in
    # substrate class after decompilation this is required to give valid reference
    # to custom actions which use them in profile/service level
    if not (variables or tasks) and (
        cls.name not in list(SUBSTRATE.VM_POWER_ACTIONS.keys())
    ):
        return ""

    """
    Brief:
    1. yields following in substrate class if any custom action uses power actions:
        def __vm_power_on__():
            pass
    2. yields "" if no custom action uses power actions.

    Detail:
    Only vm power actions skip previous check to include empty definition power actions
    in substrate class. e.g.
    def __vm_power_on__():
        pass
    This is necessary to give valid reference to custom actions using these power 
    actions in profile/service level. But if there are no custom actions using 
    power actions in any level then we don't need to include empty definition power actions.
    Therefore, returning without making power actions definition in this case by using
    get_power_action_substrate_map() which returns empty dict if there are no custom actions using
    power actions.
    """
    if cls.name in list(SUBSTRATE.VM_POWER_ACTIONS.keys()) and (
        not get_power_action_substrate_map()
    ):
        return ""

    # get rendered endpoints to be rendered by blueprint
    for ind, task in enumerate(runbook.tasks):
        ep = task.exec_target_reference
        if ep:
            if ep.name in ep_list:
                continue
            endpoints.append(render_endpoint(ep))
            ep_list.append(ep.name)
    user_attrs = {
        "name": cls.__name__,
        "description": cls.__doc__ or "",
        "tasks": tasks,
        "variables": variables,
        "endpoints": endpoints,
    }

    runbook_outputs = getattr(runbook, "outputs", [])
    if runbook_outputs:
        outputs = []
        for output in runbook.outputs:
            var_template = render_variable_template(
                output,
                entity_context,
                context=runbook_context,
                variable_context="output_variable",
            )
            outputs.append(modify_var_format(var_template))
        user_attrs["outputs"] = outputs

    if cls.type != "user":
        user_attrs["type"] = cls.type  # Only set if non-default

    gui_display_name = getattr(cls, "name", "") or cls.__name__
    if gui_display_name != cls.__name__:
        user_attrs["gui_display_name"] = gui_display_name

    text = render_template(schema_file="action.py.jinja2", obj=user_attrs)
    return text.strip()


def get_task_order(task_list):
    """
    Returns the root_node and task_child_map which is a dict containg a node mapped to all its children

    Algorithm Description:
        - After declaring all the variables - edges, task_indegree_count_map, task_edges_map
        - First we create an empty queue and add all the nodes present on the base level and at the same time
          task_name and task_data are appended to task_child_map
          q = [] -> q = [{root_node, root_node_data}, {task_name, task_data}, ....]
          task_child_map[(root_node, 0)] = [] -> task_child_map[(root_node, 0)] = [{task_name, task_data}, ....]

        - Then we start traversing by popping each element from the queue, traversing is done in level-order

        - Each node's child is traversed and is added to the queue if it has not been visited already and
          the task_name and task_data are appended to the task_child_map
          q = [..., (child_task_name, child_task_level), ...]
          task_child_map = [..., {child_task_name, child_task_data}, ...]
    """

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

    # map to store indegree of everyu task
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

    """
    task_child_map is the dict containg a node mapped to all its children
        key(tuple): (node_name, depth)
        value(list(dict)): [{child1_task_name, child1_task_data}, {child2_task_name, child2_task_data}, ...] 
    """

    # Here we are taking the name of root node as random to avoid any conflicts
    root_node = str(uuid.uuid4())
    task_child_map = {}
    q = []

    # Here we first check append all the nodes which are present on the base level to our queue
    for task_name in queue:
        if (root_node, 0) not in task_child_map:
            task_child_map[(root_node, 0)] = []
            q.append((root_node, 0))

        task_child_map[(root_node, 0)].append(
            {"task_name": task_name, "task_data": task_name_data_map[task_name]}
        )

    while q:
        n = len(q)

        # travelling level by level
        while n:
            task_key = q.pop(0)
            # Iterating through every node in the queue
            for task in task_child_map[task_key]:
                # Iterating through every child of the node
                for child in task_edges_map[task.get("task_name")]:
                    child_task_key = (task.get("task_name"), (task_key[1] + 1))
                    # if the child has not been visited before then we append it to the queue
                    if child_task_key not in task_child_map:
                        task_child_map[child_task_key] = []
                        q.append(child_task_key)

                    # appending the child to the task_child_map
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
