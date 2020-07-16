from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.task import render_task_template
from calm.dsl.decompile.parallel_task import render_parallel_task_template
from calm.dsl.decompile.variable import render_variable_template
from calm.dsl.builtins import action, ActionType, RefType
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)
RUNBOOK_ACTION_MAP = {}


def render_action_template(cls, entity_context=""):

    global RUNBOOK_ACTION_MAP
    LOG.debug("Rendering {} action template".format(cls.__name__))
    if not isinstance(cls, ActionType):
        raise TypeError("{} is not of type {}".format(cls, action))

    # Update entity context
    # TODO for now, not adding runbook to context as current mapping -is 1:1
    entity_context = entity_context + "_Action_" + cls.__name__

    runbook = cls.runbook
    # Note cls.__name__ should be used for call_runbook tasks
    RUNBOOK_ACTION_MAP[runbook.__name__] = cls.__name__

    # NOTE Not using main_task_local_reference for now,
    # bcz type of main task is "DAG"
    levelled_tasks = get_task_order(runbook.tasks)
    tasks = []
    for task_list in levelled_tasks:
        if len(task_list) != 1:
            tasks.append(
                render_parallel_task_template(
                    task_list, entity_context, RUNBOOK_ACTION_MAP
                )
            )
        else:
            tasks.append(
                render_task_template(task_list[0], entity_context, RUNBOOK_ACTION_MAP)
            )

    variables = []
    for variable in runbook.variables:
        variables.append(render_variable_template(variable, entity_context))

    if not (variables or tasks):
        return ""

    user_attrs = {
        "name": cls.__name__,
        "description": cls.__doc__ or "",
        "tasks": tasks,
        "variables": variables,
    }

    gui_display_name = getattr(cls, "name", "") or cls.__name__
    if gui_display_name != cls.__name__:
        user_attrs["gui_display_name"] = gui_display_name

    text = render_template(schema_file="action.py.jinja2", obj=user_attrs)
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
        from_task = RefType.decompile(edge["from_task_reference"])
        to_task = RefType.decompile(edge["to_task_reference"])
        task_indegree_count_map[to_task.name] += 1
        task_edges_map[from_task.name].append(to_task.name)

    # Queue to store elements having indegree 0
    queue = []

    # Push elements having indegree = 0
    for task_name, indegree in task_indegree_count_map.items():
        if indegree == 0:
            queue.append(task_name)

    # Topological sort
    while queue:

        # length of queue
        ql = len(queue)

        # Inserting task with current indegree = 0
        task_data_list = []
        for task in queue:
            task_data_list.append(task_name_data_map[task])

        if task_data_list:
            res_task_list.append(task_data_list)

        while ql:
            # Popping the element at start
            cur_task = queue.pop(0)

            # Iterating its edges, and decrease the indegree of to_edge task by 1
            for to_task in task_edges_map[cur_task]:
                task_indegree_count_map[to_task] -= 1

                # If indegree is 0, push to queue
                if task_indegree_count_map[to_task] == 0:
                    queue.append(to_task)

            # decrement the counter for queue length
            ql -= 1

    return res_task_list
