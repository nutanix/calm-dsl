from .entity import ResourceAPI


class SettingAPI(ResourceAPI):

    PREFIX = ResourceAPI.PREFIX + "accounts"
    VERIFY = PREFIX + '/{}/verify'

    def verify(self, id):
        return self.connection._call(
            self.VERIFY.format(id),
            verify=False,
            method=REQUEST.METHOD.GET
        )
