from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.task import render_task_template
from calm.dsl.decompile.parallel_task import render_parallel_task_template
from calm.dsl.decompile.variable import render_variable_template
from calm.dsl.builtins import action, ActionType


RUNBOOK_ACTION_MAP = {}


def render_action_template(cls):

    global RUNBOOK_REF_MAP
    if not isinstance(cls, ActionType):
        raise TypeError("{} is not of type {}".format(cls, action))

    runbook = cls.runbook
    RUNBOOK_ACTION_MAP[runbook.__name__] = cls.__name__

    levelled_tasks = get_task_order(runbook.tasks)

    tasks = []
    for task_list in levelled_tasks:
        if len(task_list) != 1:
            tasks.append(render_parallel_task_template(task_list, RUNBOOK_ACTION_MAP))
        else:
            tasks.append(render_task_template(task_list[0], RUNBOOK_ACTION_MAP))

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


def get_task_order(task_list):
    """Returns the list where each index represents a list of task that executes parallely"""

    # First task is dag task
    # TODO search by task type for DAG and pop it from list
    dag_task = task_list[0]
    edges = dag_task.attrs["edges"]

    # Final resultant task list with level as index
    res_task_list = []

    # map to store the edges from given  task
    task_edges_map = {}

    # map to store indegree of everyu task
    task_indegree_count_map = {}

    # create task map with name
    task_name_data_map = {}
    for task in task_list[1:]:
        task_name = task.__name__
        task_name_data_map[task_name] = task
        task_indegree_count_map[task_name] = 0
        task_edges_map[task_name] = []

    # store in degree of every task
    for edge in edges:
        from_task = edge["from_task_reference"]["name"]
        to_task = edge["to_task_reference"]["name"]
        task_indegree_count_map[to_task] += 1
        task_edges_map[from_task].append(to_task)

    # Queue to store elements having indegree queue
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
