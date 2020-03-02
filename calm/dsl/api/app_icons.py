from .resource import ResourceAPI
from .connection import REQUEST


class AppIconAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="app_icons")
        self.UPLOAD = self.PREFIX + "/upload"

    def upload(self, icon_name, file_path):
        data = {"name": icon_name}
        files = {"image": ("icon_name", open(file_path, "rb"), "image/jpeg")}

        return self.connection._call(
            self.UPLOAD, request_json=data, files=files, method=REQUEST.METHOD.POST,
        )
