import ast
import inspect
import uuid

from .task import meta
from .entity import EntityType, Entity
from .descriptor import DescriptorType
from .validator import PropertyValidator
from .variable import VariableType


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


def generate_runbook(**kwargs):

    tasks = kwargs.get("tasks")

    category = kwargs.pop("category", None)
    substrate_ips = kwargs.pop("substrate_ips", None)
    if category is not None and substrate_ips is not None:
        raise ValueError(
            "Only one of category or substrate_ips is allowed at runbook level "
            + kwargs.get("name", "")
        )
    if category is not None:
        kwargs["target_type"] = "category"
        kwargs["target_value"] = category
    if substrate_ips is not None:
        kwargs["target_type"] = "substrate_ips"
        kwargs["target_value"] = substrate_ips

    meta_task = meta(
        name=str(uuid.uuid4())[:8] + "_meta",
        child_tasks=tasks,
        edges=[],
    )
    runbook = runbook_create(**kwargs)
    runbook.main_task_local_reference = meta_task.get_ref()
    runbook.tasks = [meta_task] + tasks
    return runbook


class GetCallNodes(ast.NodeVisitor):

    # TODO: Need to add validations for unsupported nodes.
    def __init__(self, func_globals, target=None):
        self.task_list = []
        self.all_tasks = []
        self.variables = {}
        self.args = {}
        self._globals = func_globals or {}.copy()

    def get_objects(self):
        return self.all_tasks, self.variables, self.task_list, self.args

    def visit_Call(self, node, return_task=False):
        if isinstance(node.func, ast.Attribute):
            name_node = node.func
            while not isinstance(name_node, ast.Name):
                name_node = name_node.value
            if name_node.id in list(self._globals.keys()) + ["CalmTask"]:
                task = eval(compile(ast.Expression(node), "", "eval"), self._globals)
                if task is not None:
                    if return_task:
                        return task
                    self.task_list.append(task)
                    self.all_tasks.append(task)

    def visit_FunctionDef(self, node):
        args = node.args.args
        defaults = node.args.defaults
        for arg, val in zip(args, defaults):
            if arg.arg in self.args.keys():
                raise NameError("Duplicate argument name {}".format(arg.arg))
            if not isinstance(val, ast.Str):
                raise ValueError("Only arguments of type string allowed {}".format(arg.arg))
            self.args[arg.arg] = val.s

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
        if isinstance(node.value, ast.Call):
            name_node = node.value.func
            while not isinstance(name_node, ast.Name):
                name_node = name_node.value
            if name_node.id in list(self._globals.keys()) + ["CalmVariable"]:
                variable = eval(
                    compile(ast.Expression(node.value), "", "eval"), self._globals
                )
                if isinstance(variable, VariableType):
                    variable.name = variable_name
                    self.variables[variable_name] = variable

    def visit_With(self, node):
        parallel_tasks = []
        if len(node.items) > 1:
            raise ValueError(
                "Only a single context is supported in 'with' statements inside the action."
            )
        context = eval(
            compile(ast.Expression(node.items[0].context_expr), "", "eval"),
            self._globals,
        )
        if context.__calm_type__ == "parallel":
            for statement in node.body:
                if not isinstance(statement.value, ast.Call):
                    raise ValueError(
                        "Only calls to 'CalmTask' methods supported inside parallel context."
                    )
                task = self.visit_Call(statement.value, return_task=True)
                if task:
                    parallel_tasks.append(task)
                    self.all_tasks.append(task)
            self.task_list.append(parallel_tasks)
        else:
            raise ValueError(
                "Unsupported context used in 'with' statement inside the action."
            )


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

        # Get the indent since this decorator is used within class definition
        # For this we split the code on newline and count the number of spaces
        # before the @action decorator.
        # src = "    @action\n    def action1():\n    CalmTask.Exec.ssh("Hello World")"
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
        all_tasks, variables, task_list, args = node_visitor.get_objects()
        self.user_runbook = generate_runbook(name=self.runbook_name, tasks=task_list, variables=variables, **args)

        self.__parsed__ = True

        return self.user_runbook
