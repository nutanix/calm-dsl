import ast

from .entity import EntityType
from .task import CalmTask, TaskType
from .variable import CalmVariable, VariableType


class GetCallNodes(ast.NodeVisitor):

    # TODO: Need to add validations for unsupported nodes.
    def __init__(self, func_globals, target=None):
        self.task_list = []
        self.all_tasks = []
        self.variables = {}
        self.target = target or None
        self._globals = func_globals or {}.copy()

    def get_objects(self):
        return self.all_tasks, self.variables, self.task_list

    def visit_Call(self, node, return_task=False):
        sub_node = node.func
        while not isinstance(sub_node, ast.Name):
            sub_node = sub_node.value
        py_object = eval(compile(ast.Expression(sub_node), "", "eval"), self._globals)
        if py_object == CalmTask or isinstance(py_object, EntityType):
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
