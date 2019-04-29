from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler
from tornado.httpclient import AsyncHTTPClient


class HelloWorldHandler(IPythonHandler):
    async def get(self):
        # import ipdb; ipdb.set_trace()
        res = await self.client_test()
        if res:
            self.finish(res)
        else:
            self.finish("Hello, world! Calm extenstion called!!")

    async def client_test(self):
        http_client = AsyncHTTPClient()
        try:
            response = await http_client.fetch("http://www.google.com")
            return response
        except Exception as e:
            print("Error: %s" % e)
        else:
            print(response.body)


def load_jupyter_server_extension(nb_server_app):
    """
    Called when the extension is loaded.

    Args:
        nb_server_app (NotebookWebApplication): handle to the Notebook webserver instance.
    """
    print("********* Called load_jupyter_server_extension")
    web_app = nb_server_app.web_app
    host_pattern = ".*$"
    route_pattern = url_path_join(web_app.settings["base_url"], "/hello")
    web_app.add_handlers(host_pattern, [(route_pattern, HelloWorldHandler)])
