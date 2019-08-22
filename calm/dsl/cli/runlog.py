from asciimatics.widgets import Frame, Layout, Divider, Text, Button, DatePicker, TimePicker, Label
from asciimatics.scene import Scene
from asciimatics.exceptions import StopApplication
import time
from time import sleep
import itertools

from anytree import NodeMixin, RenderTree
from json import JSONEncoder
import datetime

from .constants import RUNLOG, SINGLE_INPUT


class InputFrame(Frame):
    def __init__(self, name, screen, inputs, data):
        super(InputFrame, self).__init__(screen,
                                         int(len(inputs) * 2 + 8),
                                         int(screen.width * 2 // 3),
                                         has_shadow=True,
                                         data=data,
                                         name=name)
        layout = Layout([1, len(inputs), 1])
        self.add_layout(layout)
        layout.add_widget(Label("Inputs for the input task '{}'".format(name), height=2), 1)
        for singleinput in inputs:
            if singleinput.get("input_type", SINGLE_INPUT.TYPE.TEXT) == SINGLE_INPUT.TYPE.TEXT:
                layout.add_widget(
                    Text(label=singleinput.get("name") + ":",
                         name=singleinput.get("name"),
                         on_change=self._on_change), 1)
            elif singleinput.get("input_type", SINGLE_INPUT.TYPE.TEXT) == SINGLE_INPUT.TYPE.DATE:
                layout.add_widget(
                    DatePicker(label=singleinput.get("name") + ":",
                               name=singleinput.get("name"),
                               year_range=range(1999, 2100),
                               on_change=self._on_change), 1)
            elif singleinput.get("input_type", SINGLE_INPUT.TYPE.TEXT) == SINGLE_INPUT.TYPE.TIME:
                layout.add_widget(
                    TimePicker(label=singleinput.get("name") + ":",
                               name=singleinput.get("name"),
                               seconds=True,
                               on_change=self._on_change), 1)
            elif singleinput.get("input_type", SINGLE_INPUT.TYPE.TEXT) == SINGLE_INPUT.TYPE.PASSWORD:
                layout.add_widget(
                    Text(label=singleinput.get("name") + ":",
                         name=singleinput.get("name"),
                         hide_char="*",
                         on_change=self._on_change), 1)

        layout.add_widget(Divider(height=3), 1)
        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Submit", self._submit), 1)
        self.fix()

    def _set_default(self):
        self.set_theme("bright")

    def _on_change(self):
        self.save()

    def _submit(self):
        for key, value in self.data.items():
            input_payload[key]['value'] = str(value)
        raise StopApplication("User requested exit")


class RunlogNode(NodeMixin):
    def __init__(self, runlog, machine=None, parent=None, children=None, outputs=None):
        self.runlog = runlog
        self.parent = parent
        self.outputs = outputs or []
        self.machine = machine
        if children:
            self.children = children


def displayRunLog(screen, obj, pre, line):

    if not isinstance(obj, RunlogNode):
        return super().default(obj)

    metadata = obj.runlog["metadata"]
    status = obj.runlog["status"]
    state = status["state"]
    output = ""

    idx = itertools.count(start=line, step=1).__next__

    if status["type"] == "task_runlog":
        name = status["task_reference"]["name"]
        for out in obj.outputs:
            output += "\'{}\'\n".format(out)
    elif status["type"] == "runbook_runlog":
        if "call_runbook_reference" in status:
            name = status["call_runbook_reference"]["name"]
        else:
            name = status["runbook_reference"]["name"]
    elif status["type"] == "action_runlog" and "action_reference" in status:
        name = status["action_reference"]["name"]
    elif status["type"] == "app":
        screen.print_at("{}{}".format(pre, status["name"]), 0, idx())
        return idx()
    else:
        screen.print_at("{}root".format(pre), 0, idx())
        return idx()

    # TODO - Fix KeyError for action_runlog

    if obj.machine:
        name = "{} [machine: '{}']".format(name, obj.machine)

    creation_time = int(metadata["creation_time"]) // 1000000
    username = (
        status["userdata_reference"]["name"]
        if "userdata_reference" in status
        else None
    )
    last_update_time = int(metadata["last_update_time"]) // 1000000

    prefix = "{}{} (Status:".format(pre, name)
    screen.print_at(prefix, 0, line)
    colour = 3  # yellow for pending state
    if state == RUNLOG.STATUS.SUCCESS:
        colour = 2  # green for success
    elif state in RUNLOG.FAILURE_STATES:
        colour = 1  # red for failure
    elif state == RUNLOG.STATUS.RUNNING:
        colour = 4  # blue for running state
    elif state == RUNLOG.STATUS.INPUT:
        colour = 6  # cyan for input state
    screen.print_at("{})".format(state), len(prefix) + 1, idx(), colour=colour)

    if status["type"] == "action_runlog":
        screen.print_at(
            "Runlog UUID: {}".format(metadata["uuid"]),
            len(pre) + 4, idx()
        )
    screen.print_at(
        "Started: {}".format(time.ctime(creation_time)),
        len(pre) + 4, idx()
    )

    if username:
        screen.print_at(
            "Run by: {}".format(username),
            len(pre) + 4, idx()
        )
    if state in RUNLOG.TERMINAL_STATES:
        screen.print_at(
            "Finished: {}".format(time.ctime(last_update_time)),
            len(pre) + 4, idx()
        )
    else:
        screen.print_at(
            "Last Updated: {}".format(time.ctime(last_update_time)),
            len(pre) + 4, idx()
        )

    if output and not obj.children:
        screen.print_at("Output :", len(pre) + 4, idx())
        output_lines = output.splitlines()
        for line in output_lines:
            screen.print_at(line, len(pre) + 6, idx(), colour=5, attr=1)

    if status["type"] == "task_runlog" and state == RUNLOG.STATUS.INPUT:
        attrs = status.get("attrs", None)
        if not isinstance(attrs, dict):
            return idx()

        input_tasks.append({"name": name,
                            "uuid": metadata["uuid"],
                            "inputs": attrs.get("inputs", [])})
    return idx()


class RunlogJSONEncoder(JSONEncoder):
    def default(self, obj):

        if not isinstance(obj, RunlogNode):
            return super().default(obj)

        metadata = obj.runlog["metadata"]
        status = obj.runlog["status"]
        state = status["state"]
        output = ""

        if status["type"] == "task_runlog":
            name = status["task_reference"]["name"]
            for out in obj.outputs:
                output += "\'{}\'\n".format(out)
        elif status["type"] == "runbook_runlog":
            if "call_runbook_reference" in status:
                name = status["call_runbook_reference"]["name"]
            else:
                name = status["runbook_reference"]["name"]
        elif status["type"] == "action_runlog" and "action_reference" in status:
            name = status["action_reference"]["name"]
        elif status["type"] == "app":
            return status["name"]
        else:
            return "root"

        # TODO - Fix KeyError for action_runlog

        creation_time = int(metadata["creation_time"]) // 1000000
        username = (
            status["userdata_reference"]["name"]
            if "userdata_reference" in status
            else None
        )
        last_update_time = int(metadata["last_update_time"]) // 1000000

        encodedStringList = []
        encodedStringList.append("{} (Status: {})".format(name, state))
        if status["type"] == "action_runlog":
            encodedStringList.append("\tRunlog UUID: {}".format(metadata["uuid"]))
        encodedStringList.append("\tStarted: {}".format(time.ctime(creation_time)))

        if username:
            encodedStringList.append("\tRun by: {}".format(username))
        if state in RUNLOG.TERMINAL_STATES:
            encodedStringList.append(
                "\tFinished: {}".format(time.ctime(last_update_time))
            )
        else:
            encodedStringList.append(
                "\tLast Updated: {}".format(time.ctime(last_update_time))
            )

        if output:
            encodedStringList.append("\tOutput :")
            output_lines = output.splitlines()
            for line in output_lines:
                encodedStringList.append("\t\t{}".format(line))

        return "\n".join(encodedStringList)


def get_completion_func(screen):
    def is_action_complete(response, client=None, input_data={}, **kwargs):

        global input_tasks
        global input_payload
        input_tasks = []
        entities = response["entities"]
        if len(entities):

            # Sort entities based on creation time
            sorted_entities = sorted(
                entities, key=lambda x: int(x["metadata"]["creation_time"])
            )

            # Create nodes of runlog tree and a map based on uuid
            root = None
            nodes = {}
            for runlog in sorted_entities:
                # Create root node
                # TODO - Get details of root node
                if not root:
                    root_uuid = runlog["status"]["root_reference"]["uuid"]
                    root_runlog = {
                        "metadata": {"uuid": root_uuid},
                        "status": {"type": "action_runlog", "state": ""},
                    }
                    root = RunlogNode(root_runlog)
                    nodes[str(root_uuid)] = root

                uuid = runlog["metadata"]["uuid"]
                outputs = []
                machine = runlog['status'].get("machine_name", None)
                if client is not None and runlog['status']['type'] == "task_runlog" and not runlog["status"].get("attrs", None):
                    res, err = client.runbook.runlog_output(uuid)
                    if err:
                        raise Exception("\n[{}] - {}".format(err["code"], err["error"]))
                    runlog_output = res.json()
                    output_list = runlog_output['status']['output_list']
                    for task_output in output_list:
                        outputs.append(task_output["output"])
                nodes[str(uuid)] = RunlogNode(runlog, parent=root, outputs=outputs, machine=machine)

            # Attach parent to nodes
            for runlog in sorted_entities:
                uuid = runlog["metadata"]["uuid"]
                parent_uuid = runlog["status"]["parent_reference"]["uuid"]
                node = nodes[str(uuid)]
                node.parent = nodes[str(parent_uuid)]

            # Show Progress
            # TODO - Draw progress bar
            total_tasks = 0
            completed_tasks = 0
            for runlog in sorted_entities:
                runlog_type = runlog["status"]["type"]
                if runlog_type == "task_runlog":
                    total_tasks += 1
                    state = runlog["status"]["state"]
                    if state in RUNLOG.STATUS.SUCCESS:
                        completed_tasks += 1

            if total_tasks:
                screen.clear()
                progress = "{0:.2f}".format(completed_tasks / total_tasks * 100)
                screen.print_at("Progress: {}%".format(progress), 0, 0)

            # Render Tree on next line
            line = 1
            for pre, _, node in RenderTree(root):
                line = displayRunLog(screen, node, pre, line)
            screen.refresh()

            # Check if any tasks is in INPUT state
            if len(input_tasks) > 0:
                sleep(2)
                for input_task in input_tasks:
                    name = input_task.get("name", "")
                    inputs = input_task.get("inputs", [])
                    task_uuid = input_task.get("uuid", "")
                    input_payload = {}
                    data = {}
                    inputs_required = []
                    input_value = input_data.get(name, {})
                    for singleinput in inputs:
                        input_type = singleinput.get("input_type", SINGLE_INPUT.TYPE.TEXT)
                        input_name = singleinput.get("name", "")
                        value = input_value.get(input_name, "")
                        if not value:
                            inputs_required.append(singleinput)
                            data.update({input_name: ""})
                        input_payload.update({input_name: {"secret": False, "value": value}})
                        if input_type == SINGLE_INPUT.TYPE.PASSWORD:
                            input_payload.update({input_name: {"secret": True, "value": value}})
                        elif input_type == SINGLE_INPUT.TYPE.DATE:
                            data.update({input_name: datetime.datetime.now().date()})
                        elif input_type == SINGLE_INPUT.TYPE.TIME:
                            data.update({input_name: datetime.datetime.now().time()})
                    if len(inputs_required) > 0:
                        screen.play([Scene([InputFrame(name, screen, inputs_required, data)], -1)])
                    if client is not None:
                        client.runbook.resume(task_uuid, input_payload)
                input_tasks = []
                screen.clear()
                if total_tasks:
                    progress = "{0:.2f}".format(completed_tasks / total_tasks * 100)
                    screen.print_at("Progress: {}%".format(progress), 0, 0)

                line = 1
                for pre, _, node in RenderTree(root):
                    line = displayRunLog(screen, node, pre, line)
                screen.print_at("Sending resume for input tasks with input values", 0, line, colour=6)
                line = line + 1
                screen.refresh()

            for runlog in sorted_entities:
                state = runlog["status"]["state"]
                if state in RUNLOG.FAILURE_STATES:
                    msg = "Action failed. Exit screen? (y)"
                    screen.print_at(msg, 0, line)
                    screen.refresh()
                    return (True, msg)
                if state not in RUNLOG.TERMINAL_STATES:
                    return (False, "")

            msg = "Action ran successfully. Exit screen? (y)"
            screen.print_at(msg, 0, line)
            screen.refresh()

            return (True, msg)
        return (False, "")

    return is_action_complete


def get_runlog_status(screen):
    def check_runlog_status(response, client=None, **kwargs):

        if response["status"]["state"] == "PENDING":
            msg = ">> Runlog run is in PENDING state"
            screen.print_at(msg, 0, 0)
            screen.refresh()
        elif response["status"]["state"] in RUNLOG.FAILURE_STATES:
            msg = ">> Runlog run is in {} state.".format(response["status"]["state"])
            msg += " {}".format("\n".join(response["status"]["reason_list"]))
            screen.print_at(msg, 0, 0)
            screen.refresh()
            return (True, msg)
        else:
            return (True, "")
        return (False, msg)

    return check_runlog_status
