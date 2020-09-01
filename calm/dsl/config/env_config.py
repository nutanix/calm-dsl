import os


class EnvConfig:
    pc_ip = os.environ.get("PC_IP") or ""
    pc_port = os.environ.get("PC_PORT") or ""
    pc_username = os.environ.get("PC_USER") or ""
    pc_password = os.environ.get("PC_PASSWORD") or ""

    @classmethod
    def get_server_config(cls):

        return {
            "pc_ip": cls.pc_ip,
            "pc_port": cls.pc_port,
            "pc_username": cls.pc_username,
            "pc_password": cls.pc_password,
        }

    # Support for project and log config in enviroinment hasn't been added
