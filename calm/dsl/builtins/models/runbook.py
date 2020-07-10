import ast
import inspect

from .ref import ref
from .task import dag
from .entity import EntityType, Entity
from .endpoint import EndpointType
from .credential import CredentialType
from .ref import RefType
from .descriptor import DescriptorType
from .validator import PropertyValidator
from .node_visitor import GetCallNodes


class RunbookType(EntityType):
    __schema_name__ = "Runbook"
    __openapi_type__ = "app_runbook"

    def __call__(*args, **kwargs):
        pass

    @classmethod
    def pre_decompile(mcls, cdict, context=[]):

        cdict = super().pre_decompile(cdict, context=context)
        # Removing additional attributes
        cdict.pop("state", None)
        cdict.pop("message_list", None)
        return cdict


class RunbookValidator(PropertyValidator, openapi_type="app_runbook"):
    __default__ = None
    __kind__ = RunbookType


def _runbook(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return RunbookType(name, bases, kwargs)


Runbook = _runbook()


def runbook_create(**kwargs):
    name = kwargs.get("name", kwargs.get("__name__", None))
    bases = (Entity,)
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
        self.action_name = user_func.__name__
        self.action_description = user_func.__doc__ or ""
        self.user_func = user_func
        self.user_runbook = None
        self.__parsed__ = False
        if self.__class__ == runbook:
            self.__get__()

    def __call__(self, name=None):
        pass

    def __get__(self, instance=None, cls=None):
        """
        Translate the user defined function to an runbook.
        Args:
            instance (object): Instance of cls
            cls (Entity): Entity that this runbook is defined on
        Returns:
            (RunbookType): Generated Runbook class
        """
        if self.__parsed__:
            return self.runbook

        # Get the source code for the user function.
        # Also replace tabs with 4 spaces.
        src = inspect.getsource(self.user_func).replace("\t", "    ")

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

        # for runbooks updating func_globals with endpoints and credentials passed in kwargs
        if self.__class__ == runbook:
            args = dict()
            sig = inspect.signature(self.user_func)
            for name, param in sig.parameters.items():
                args[name] = param.default
            if args.get("credentials", []):
                func_globals.update({"credentials": args["credentials"]})
            if args.get("endpoints", []):
                func_globals.update({"endpoints": args["endpoints"]})

        node_visitor = GetCallNodes(
            func_globals,
            target=cls.get_task_target() if hasattr(cls, "get_task_target") else None,
            is_runbook=True if self.__class__ == runbook else False,
        )
        try:
            node_visitor.visit(node)
        except Exception as ex:
            self.__exception__ = ex
            raise
        tasks, variables, task_list = node_visitor.get_objects()
        edges = []
        child_tasks = []

        def create_edges(_task_list, from_task=None):

            if len(_task_list) == 0:
                return
            to_tasks = _task_list[0]
            if not isinstance(to_tasks, list):
                to_tasks = [to_tasks]
            for to_task in to_tasks:
                if isinstance(to_task, list):
                    create_edges(to_task, from_task=from_task)
                else:
                    child_tasks.append(to_task)
                    if from_task:
                        edges.append((from_task.get_ref(), to_task.get_ref()))

            for from_tasks, to_tasks in zip(_task_list, _task_list[1:]):
                if not isinstance(from_tasks, list):
                    from_tasks = [from_tasks]
                if not isinstance(to_tasks, list):
                    to_tasks = [to_tasks]
                for to_task in to_tasks:
                    if not isinstance(to_task, list):
                        child_tasks.append(to_task)
                    for from_task in from_tasks:
                        if isinstance(from_task, list):
                            raise ValueError(
                                "Tasks are not supported after parallel in runbooks"
                            )
                        if isinstance(to_task, list) and len(from_tasks) == 1:
                            create_edges(to_task, from_task=from_task)
                        else:
                            edges.append((from_task.get_ref(), to_task.get_ref()))

        create_edges(task_list)
        # Note - Server checks for name uniqueness in runbooks across actions
        # Generate unique names using class name and func name.
        prefix = (
            cls.__name__ + "_" + self.user_func.__name__
            if hasattr(cls, "__name__")
            else "" + self.user_func.__name__
        )
        runbook_name = prefix + "_runbook"
        dag_name = prefix + "_dag"

        # First create the dag
        self.user_dag = dag(
            name=dag_name,
            child_tasks=child_tasks if self.__class__ == runbook else tasks,
            edges=edges,
            target=cls.get_task_target()
            if getattr(cls, "__has_dag_target__", True)
            and hasattr(cls, "get_task_target")
            else None,
        )

        # Modify the user runbook
        self.user_runbook = runbook_create(**{"name": runbook_name})
        self.user_runbook.main_task_local_reference = self.user_dag.get_ref()
        self.user_runbook.tasks = [self.user_dag] + tasks
        self.user_runbook.variables = [variable for variable in variables.values()]

        # Finally create the runbook service, only for runbook class not action
        if self.__class__ == runbook:
            args = dict()
            sig = inspect.signature(self.user_func)
            for name, param in sig.parameters.items():
                args[name] = param.default

            from .runbook_service import _runbook_service_create

            self.runbook = _runbook_service_create(**{"runbook": self.user_runbook})

            credentials = args.pop("credentials", [])
            endpoints = args.pop("endpoints", [])
            default_target = args.pop("default", 0)

            for arg in args:
                raise ValueError("{} is an unexpected argument.".format(arg))

            if not isinstance(credentials, list):
                raise TypeError("{} is not of type {}".format(credentials, list))
            for cred in credentials:
                if not isinstance(cred, CredentialType):
                    raise TypeError("{} is not of type {}".format(cred, EndpointType))

            if not isinstance(endpoints, list):
                raise TypeError("{} is not of type {}".format(endpoints, list))
            for ep in endpoints:
                if not isinstance(ep, EndpointType):
                    raise TypeError("{} is not of type {}".format(ep, EndpointType))
                if not ep.type:
                    raise ValueError(
                        "Existing endpoint {} are not allowed in endpoints argument.".format(
                            ep
                        )
                    )

            if default_target is not False:
                if not isinstance(default_target, RefType) and not isinstance(
                    default_target, int
                ):
                    raise TypeError(
                        "{} is not of type {} or {}".format(
                            default_target, RefType, "Integer"
                        )
                    )
                elif isinstance(default_target, RefType):
                    self.runbook.default_target = default_target
                elif len(endpoints) > 0:
                    if len(endpoints) <= int(default_target):
                        raise TypeError(
                            "No Endpoint preset at {} index for default Target".format(
                                int(default_target)
                            )
                        )
                    self.runbook.default_target = ref(endpoints[int(default_target)])

            self.runbook.credentials = credentials
            self.runbook.endpoints = endpoints
            self.__parsed__ = True
            return self.runbook

        else:
            return self.user_runbook


# helper function to get runbook json dump
def runbook_json(DslRunbook):

    if not isinstance(DslRunbook, runbook):
        raise TypeError("{} is not of type {}".format(DslRunbook, runbook))
    return DslRunbook.runbook.json_dumps(pprint=True)


class branch:
    __calm_type__ = "branch"

    def __new__(cls, *args, **kwargs):
        return cls
