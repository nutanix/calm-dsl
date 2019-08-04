import time
import json

from anytree import NodeMixin, RenderTree
from json import JSONEncoder

from .constants import RUNLOG


class RunlogNode(NodeMixin):
    def __init__(self, runlog, parent=None, children=None, outputs=None):
        self.runlog = runlog
        self.parent = parent
        self.outputs = outputs or []
        if children:
            self.children = children


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
    def is_action_complete(response, client=None):

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
                if client is not None and runlog['status']['type'] == "task_runlog":
                    res, err = client.runbook.runlog_output(uuid)
                    if err:
                        raise Exception("\n[{}] - {}".format(err["code"], err["error"]))
                    runlog_output = res.json()
                    output_list = runlog_output['status']['output_list']
                    for task_output in output_list:
                        outputs.append(task_output["output"])
                nodes[str(uuid)] = RunlogNode(runlog, parent=root, outputs=outputs)

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
                lines = json.dumps(node, cls=RunlogJSONEncoder).split("\\n")
                for linestr in lines:
                    tabcount = linestr.count("\\t")
                    if not tabcount:
                        screen.print_at("{}{}".format(pre, linestr), 0, line)
                    else:
                        screen.print_at(
                            "{}{}".format("", linestr.replace("\\t", "")),
                            len(pre) + 2 + tabcount * 2,
                            line,
                        )
                    line += 1
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
    def check_runlog_status(response, client=None):


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
