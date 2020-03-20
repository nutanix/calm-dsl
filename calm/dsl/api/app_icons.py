from .resource import ResourceAPI
from .connection import REQUEST


class AppIconAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(connection, resource_type="app_icons")
        self.UPLOAD = self.PREFIX + "/upload"
        self.IS_MARKETPLACE_ICON = self.PREFIX + "/{}/" + "is_marketplaceicon"

    def upload(self, icon_name, file_path):
        data = {"name": icon_name}
        files = {"image": (icon_name, open(file_path, "rb"), "image/jpeg")}

        return self.connection._call(
            self.UPLOAD,
            request_json=data,
            files=files,
            method=REQUEST.METHOD.POST,
            verify=False,
        )

    def is_marketplace_icon(self, uuid):
        return self.connection._call(
            self.IS_MARKETPLACE_ICON.format(uuid),
            verify=False,
            method=REQUEST.METHOD.GET,
        )
