from .resource import ResourceAPI
from .connection import REQUEST

class AppIconAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="app_icons")
        self.UPLOAD = self.PREFIX + "/upload"

    def upload(self, icon_name, file_path):
        data = {"name": icon_name}
        file_list = [
            ("image", open(file_path, "rb"))
        ]

        return self.connection._call(
            self.UPLOAD,
            verify=False,
            request_json=data,
            files=file_list,
            method=REQUEST.METHOD.POST,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
