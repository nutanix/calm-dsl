import ast
import uuid

from .task import meta
from .entity import EntityType
from .task import CalmTask, RunbookTask, TaskType
from .variable import CalmVariable, RunbookVariable, VariableType


def handle_meta_create(node, func_globals, prefix=None):
    """
    helper for create parsing tasks and creating meta
    """

    node_visitor = GetCallNodes(func_globals, is_runbook=True, is_metatask_context=True)
    try:
        node_visitor.visit(node)
    except Exception as ex:
        raise ex
    tasks, variables, task_list = node_visitor.get_objects()

    child_tasks = []
    for child_task in task_list:
        if not isinstance(child_task, list):
            child_task = [child_task]
        child_tasks.extend(child_task)

    # First create the meta
    if prefix is None:
        prefix = str(uuid.uuid4())[-10:]
    user_meta = meta(name=prefix + "_meta_task", child_tasks=child_tasks)

    return user_meta, tasks, variables


class GetCallNodes(ast.NodeVisitor):

    # TODO: Need to add validations for unsupported nodes.
    def __init__(
        self, func_globals, target=None, is_runbook=False, is_metatask_context=False
    ):
        self.task_list = []
        self.all_tasks = []
        self.variables = {}
        self.target = target or None
        self._globals = func_globals or {}.copy()

        # flag to check if this runbook is in context of RaaS, as decision, while, parallel tasks are supported only in RaaS
        self.is_runbook = is_runbook

        # flag to check if tasks are in context of metatask
        self.is_metatask = is_metatask_context

    def get_objects(self):
        return self.all_tasks, self.variables, self.task_list

    def visit_Call(self, node, return_task=False):
        sub_node = node.func
        while not isinstance(sub_node, ast.Name):
            sub_node = sub_node.value
        py_object = eval(compile(ast.Expression(sub_node), "", "eval"), self._globals)
        if py_object == CalmTask or RunbookTask or isinstance(py_object, EntityType):
            task = eval(compile(ast.Expression(node), "", "eval"), self._globals)
            if task is not None and isinstance(task, TaskType):
                if self.target is not None and not task.target_any_local_reference:
                    task.target_any_local_reference = self.target
                if return_task:
                    return task
                self.task_list.append(task)
                self.all_tasks.append(task)
                return
        return self.generic_visit(node)

    def visit_Assign(self, node):
        if not isinstance(node.value, ast.Call):
            return self.generic_visit(node)
        sub_node = node.value.func
        while not isinstance(sub_node, ast.Name):
            sub_node = sub_node.value
        if (
            eval(compile(ast.Expression(sub_node), "", "eval"), self._globals)
            == CalmVariable
            or eval(compile(ast.Expression(sub_node), "", "eval"), self._globals)
            == RunbookVariable
        ):
            if len(node.targets) > 1:
                raise ValueError(
                    "not enough values to unpack (expected {}, got 1)".format(
                        len(node.targets)
                    )
                )
            variable_name = node.targets[0].id
            if variable_name in self.variables.keys():
                raise NameError("duplicate variable name {}".format(variable_name))
            variable = eval(
                compile(ast.Expression(node.value), "", "eval"), self._globals
            )
            if isinstance(variable, VariableType):
                variable.name = variable_name
                self.variables[variable_name] = variable
                return
        return self.generic_visit(node)

    def visit_With(self, node):
        if len(node.items) > 1:
            raise ValueError(
                "Only a single context is supported in 'with' statements inside the action."
            )
        context = eval(
            compile(ast.Expression(node.items[0].context_expr), "", "eval"),
            self._globals,
        )
        if (
            not self.is_runbook
            and hasattr(context, "__calm_type__")
            and context.__calm_type__ == "parallel"
        ):
            parallel_tasks = []
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

        # for parallel tasks in runbooks
        elif (
            self.is_runbook
            and hasattr(context, "__calm_type__")
            and context.__calm_type__ == "parallel"
        ):
            if self.is_metatask:
                raise ValueError(
                    "parallel is not supported in runbooks under decision or loop task context."
                )
            if not node.items[0].optional_vars:
                raise ValueError(
                    "Parallel task must be used in the format `with parallel as p`"
                )
            _globals = self._globals.copy()
            var = node.items[0].optional_vars.id
            _globals.update({var: "var"})

            parallel_tasks = []

            for statement in node.body:
                if not isinstance(statement, ast.With) or len(statement.items) > 1:
                    raise ValueError(
                        "Only a single context is supported in 'with' statements inside the parallel."
                    )
                statement_context = statement.items[0].context_expr
                if (
                    len(statement_context.args) != 1
                    or not isinstance(statement_context.args[0], ast.Name)
                    or statement_context.args[0].id != var
                ):
                    raise ValueError(
                        "Incorrect argument is passed in 'branch()', use 'with branch({})'".format(
                            var
                        )
                    )
                statementContext = eval(
                    compile(ast.Expression(statement_context), "", "eval"), _globals
                )
                if (
                    hasattr(statementContext, "__calm_type__")
                    and statementContext.__calm_type__ == "branch"
                ):
                    statementBody = ast.FunctionDef(
                        body=statement.body, col_offset=statement.col_offset
                    )
                    _node_visitor = GetCallNodes(self._globals, is_runbook=True)
                    try:
                        _node_visitor.visit(statementBody)
                    except Exception as ex:
                        raise ex
                    tasks, variables, task_list = _node_visitor.get_objects()
                    if len(task_list) == 0:
                        raise ValueError(
                            "Atleast one task is required under parallel branch"
                        )
                    parallel_tasks.append(task_list)
                    self.all_tasks.extend(tasks)
                    self.variables.update(variables)
                else:
                    raise ValueError(
                        "Only with branch() contexts are supported under parallel context."
                    )

            if len(parallel_tasks) > 0:
                self.task_list.append(parallel_tasks)

        # for decision tasks
        elif (
            self.is_runbook
            and isinstance(context, TaskType)
            and context.type == "DECISION"
        ):
            if not node.items[0].optional_vars:
                raise ValueError(
                    "Decision task must be used in the format `with Task.Decision() as val`"
                )
            var = node.items[0].optional_vars.id
            success_path = None
            failure_path = None
            for statement in node.body:

                if (
                    isinstance(statement, ast.If)
                    and isinstance(statement.test, ast.Compare)
                    and statement.test.left.value.id == var
                    and statement.test.left.attr == "exit_code"
                    and isinstance(statement.test.ops[0], ast.Eq)
                    and isinstance(statement.test.comparators[0], ast.Num)
                ):

                    if (
                        len(statement.test.comparators) != 1
                        or not isinstance(statement.test.comparators[0], ast.Num)
                        or statement.test.comparators[0].n not in [0, 1]
                    ):
                        raise ValueError(
                            "Decision task on supports only exit_code 0 and 1."
                        )

                    if statement.orelse:
                        raise ValueError(
                            "elif or else are not supported in 'if {}.exit_code == 0/1'".format(
                                var
                            )
                        )

                    if statement.test.comparators[0].n == 0:
                        if success_path:
                            raise ValueError(
                                "'True' flow is defined more than once in {} task.".format(
                                    context.name
                                )
                            )
                        success_path, tasks, variables = handle_meta_create(
                            statement, self._globals, prefix=context.name + "_success"
                        )
                        self.all_tasks.extend([success_path] + tasks)
                        self.variables.update(variables)

                    elif statement.test.comparators[0].n == 1:
                        if failure_path:
                            raise ValueError(
                                "'False' flow is defined more than once in {} task.".format(
                                    context.name
                                )
                            )
                        failure_path, tasks, variables = handle_meta_create(
                            statement, self._globals, prefix=context.name + "_failure"
                        )
                        self.all_tasks.extend([failure_path] + tasks)
                        self.variables.update(variables)

                elif (
                    isinstance(statement, ast.If)
                    and isinstance(statement.test, ast.Attribute)
                    and statement.test.value.id == var
                    and statement.test.attr == "ok"
                ):

                    if success_path:
                        raise ValueError(
                            "'True' flow is defined more than once in {} task.".format(
                                context.name
                            )
                        )
                    ifBody = ast.FunctionDef(
                        body=statement.body, col_offset=node.col_offset
                    )
                    success_path, tasks, variables = handle_meta_create(
                        ifBody, self._globals, prefix=context.name + "_success"
                    )
                    self.all_tasks.extend([success_path] + tasks)
                    self.variables.update(variables)

                    if statement.orelse:
                        if failure_path:
                            raise ValueError(
                                "'False' flow is defined more than once in {} task.".format(
                                    context.name
                                )
                            )
                        elseBody = ast.FunctionDef(
                            body=statement.orelse, col_offset=node.col_offset
                        )
                        failure_path, tasks, variables = handle_meta_create(
                            elseBody, self._globals, prefix=context.name + "_failure"
                        )
                        self.all_tasks.extend([failure_path] + tasks)
                        self.variables.update(variables)

                else:
                    raise ValueError(
                        "Only 'if {}.exit_code == 0/1' or 'if {}.ok' statements are supported in decision context".format(
                            var, var
                        )
                    )

            if not success_path or not failure_path:
                raise ValueError(
                    "Both 'True' and 'False' flows are required for decision task."
                )

            context.attrs["success_child_reference"] = success_path.get_ref()
            context.attrs["failure_child_reference"] = failure_path.get_ref()
            self.all_tasks.append(context)
            self.task_list.append(context)

        # for while tasks
        elif (
            self.is_runbook
            and isinstance(context, TaskType)
            and context.type == "WHILE_LOOP"
        ):
            whileBody = ast.FunctionDef(body=node.body, col_offset=node.col_offset)
            meta_task, tasks, variables = handle_meta_create(
                whileBody, self._globals, prefix=context.name + "_loop"
            )
            self.all_tasks.extend([meta_task] + tasks)
            self.variables.update(variables)
            context.child_tasks_local_reference_list.append(meta_task.get_ref())
            self.all_tasks.append(context)
            self.task_list.append(context)
        else:
            raise ValueError(
                "Unsupported context used in 'with' statement inside the action."
            )
