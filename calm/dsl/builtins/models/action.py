import ast
import inspect
import uuid

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .task import dag

# Action - Since action, runbook and DAG task are heavily coupled together,
# the action type behaves as all three.


class RunbookType(EntityType):
    __schema_name__ = "Runbook"
    __openapi_type__ = "app_runbook"

    def __call__(*args, **kwargs):
        pass


class RunbookValidator(PropertyValidator, openapi_type="app_runbook"):
    __default__ = None
    __kind__ = RunbookType


def _runbook(**kwargs):
    name = getattr(RunbookType, "__schema_name__")
    bases = (Entity,)
    return RunbookType(name, bases, kwargs)


Runbook = _runbook()


def _runbook_create(**kwargs):

    # This follows UI naming convention for runbooks
    name = str(uuid.uuid4())[:8] + "_" + getattr(RunbookType, "__schema_name__")
    name = kwargs.get("name", kwargs.get("__name__", name))
    bases = (Runbook,)
    return RunbookType(name, bases, kwargs)


class ActionType(EntityType):
    __schema_name__ = "Action"
    __openapi_type__ = "app_action"

    def __call__(*args, **kwargs):
        pass


class ActionValidator(PropertyValidator, openapi_type="app_action"):
    __default__ = None
    __kind__ = ActionType


def _action(**kwargs):
    name = getattr(ActionType, "__schema_name__")
    bases = (Entity,)
    return ActionType(name, bases, kwargs)


Action = _action()


def _action_create(**kwargs):
    name = str(uuid.uuid4())[:8] + "_" + getattr(ActionType, "__schema_name__")
    name = kwargs.get("name", kwargs.get("__name__", name))
    bases = (Action,)
    return ActionType(name, bases, kwargs)


class GetCallNodes(ast.NodeVisitor):
    def __init__(self, func_globals):
        self.tasks = []
        self.variables = {}
        self._globals = func_globals or {}.copy()

    def get_objects(self):
        return self.tasks, self.variables

    def visit_Call(self, node):
        if node.func.id in ["exec_ssh"]:
            self.tasks.append(
                eval(compile(ast.Expression(node), "", "eval"), self._globals)
            )

    def visit_Assign(self, node):
        if len(node.targets) > 1:
            raise ValueError(
                "not enough values to unpack (expected {}, got 1)".format(
                    len(node.targets)
                )
            )
        variable_name = node.targets[0].id
        if variable_name in self.variables.keys():
            raise NameError("duplicate variable name {}".format(variable_name))
        if isinstance(node.value, ast.Call) and node.value.func.id in ["var"]:
            variable = eval(
                compile(ast.Expression(node.value), "", "eval"), self._globals
            )
            variable.name = variable_name
            self.variables[variable_name] = variable


def action(user_func):
    """
    A decorator for generating actions from a function definition.
    Args:
        entity (Entity): Entity for which this action is defined
    Returns:

    """

    # Get the entity names
    action_name = " ".join(user_func.__name__.lower().split("_")).title()
    runbook_name = str(uuid.uuid4())[:8] + "_runbook"
    dag_name = str(uuid.uuid4())[:8] + "_dag"

    # Get the source code for the user function
    src = inspect.getsource(user_func).replace("\t", "    ")

    # Get the padding since this decorator is used within class definition
    padding = src.split("\n")[0].rstrip(" ").split(" ").count("")

    # Get the function source without the decorator
    new_src = "\n".join(line[padding:] for line in src.split("\n")[1:])

    # Get all the child tasks
    node = ast.parse(new_src)
    node_visitor = GetCallNodes(user_func.__globals__)
    node_visitor.visit(node)
    tasks, variables = node_visitor.get_objects()

    # First create the dag
    edges = [(frm.get_ref(), to.get_ref()) for frm, to in zip(tasks, tasks[1:])]
    user_dag = dag(name=dag_name, child_tasks=tasks, edges=edges)

    # Next, create the RB
    user_runbook = _runbook_create(
        **{
            "main_task_local_reference": user_dag.get_ref(),
            "tasks": [user_dag] + tasks,
            "name": runbook_name,
            "variables": variables.values(),
        }
    )

    # Finally the action
    user_action = _action_create(
        **{
            "name": action_name,
            "critical": False,
            "type": "user",
            "runbook": user_runbook,
        }
    )

    return user_action
