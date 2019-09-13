import ast
import inspect
import uuid

from .task import dag
from .entity import EntityType, Entity
from .descriptor import DescriptorType
from .validator import PropertyValidator
from .node_visitor import GetCallNodes


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


def runbook_create(**kwargs):

    # This follows UI naming convention for runbooks
    name = str(uuid.uuid4())[:8] + "_" + getattr(RunbookType, "__schema_name__")
    name = kwargs.get("name", kwargs.get("__name__", name))
    bases = (Runbook,)
    return RunbookType(name, bases, kwargs)


class runbook(metaclass=DescriptorType):
    """
    runbook descriptor
    """

    def __init__(self, user_func):
        """
        A decorator for generating runbooks from a function definition.
        Args:
            user_func (function): User defined function
        Returns:
            (Runbook): Runbook class
        """

        # Generate the entity names
        self.runbook_name = user_func.__name__
        self.dag_name = str(uuid.uuid4())[:8] + "_dag"
        self.user_func = user_func
        self.__parsed__ = False

    def __call__(self, name=None):
        pass

    def __get__(self, instance, cls):
        """
        Translate the user defined function to an runbook.
        Args:
            instance (object): Instance of cls
            cls (Entity): Entity that this runbook is defined on
        Returns:
            (RunbookType): Generated Runbook class
        """
        if cls is None:
            return self

        if self.__parsed__:
            return self.user_runbook

        # Get the source code for the user function.
        # Also replace tabs with 4 spaces.
        src = inspect.getsource(self.user_func).replace("\t", "    ")
        args = {}
        sign = inspect.signature(self.user_func)
        for name, param in sign.parameters.items():
            if param.default != inspect._empty:
                args[name] = param.default

        # Get the indent since this decorator is used within class definition
        # For this we split the code on newline and count the number of spaces
        # before the @runbook decorator.
        # src = "    @runbook\n    def runbook1():\n    CalmTask.Exec.ssh("Hello World")"
        # The indentation here would be 4.
        padding = src.split("\n")[0].rstrip(" ").split(" ").count("")

        # This recreates the source code without the indentation and the
        # decorator.
        new_src = "\n".join(line[padding:] for line in src.split("\n")[1:])

        # Get all the child tasks by parsing the source code and visiting the
        # ast.Call nodes. ast.Assign nodes become variables.
        node = ast.parse(new_src)
        func_globals = self.user_func.__globals__.copy()
        node_visitor = GetCallNodes(func_globals)
        try:
            node_visitor.visit(node)
        except Exception as ex:
            self.__exception__ = ex
            raise
        tasks, variables, task_list = node_visitor.get_objects()
        edges = []
        for from_tasks, to_tasks in zip(task_list, task_list[1:]):
            if not isinstance(from_tasks, list):
                from_tasks = [from_tasks]
            if not isinstance(to_tasks, list):
                to_tasks = [to_tasks]
            for from_task in from_tasks:
                for to_task in to_tasks:
                    edges.append((from_task.get_ref(), to_task.get_ref()))

        # First create the dag
        self.user_dag = dag(
            name=self.dag_name,
            child_tasks=tasks,
            edges=edges
        )

        category = args.pop("category", None)
        substrate_ips = args.pop("substrate_ips", None)
        if category is not None and substrate_ips is not None:
            raise ValueError(
                "Only one of category or substrate_ips is allowed at runbook level "
                + self.runbook_name
            )

        kwargs = {}
        if category is not None:
            kwargs["target_type"] = "category"
            kwargs["target_value"] = category
        if substrate_ips is not None:
            kwargs["target_type"] = "substrate_ips"
            kwargs["target_value"] = substrate_ips
        kwargs["name"] = self.runbook_name

        # Modify the user runbook
        self.user_runbook = runbook_create(**kwargs)
        self.user_runbook.main_task_local_reference = self.user_dag.get_ref()
        self.user_runbook.tasks = [self.user_dag] + tasks
        self.user_runbook.variables = [variable for variable in variables.values()]

        self.__parsed__ = True

        return self.user_runbook
