import multiprocessing
from typing import Any, Dict

from gunicorn.app.wsgiapp import WSGIApplication

from src import ConfigLoader


class StandaloneApplication(WSGIApplication):
    def __init__(self, app_uri: str, options: Dict[str, Any] = None) -> None:
        self.app_uri = app_uri
        self.options = options or {}
        super().__init__()

    def load_config(self) -> None:
        config = {key: value for key, value in self.options.items() if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)


def entrypoint():
    wsgi_conf = ConfigLoader("config/webserver.toml")
    options = {
        "bind": wsgi_conf["app.bind"],
        "workers": wsgi_conf.get("app.workers", 0) or multiprocessing.cpu_count() * 2 + 1,
        "worker_class": "uvicorn.workers.UvicornWorker",
        "reload": wsgi_conf.get("dev.reload", False),
    }
    if wsgi_conf["ssl.enabled"]:
        options["certfile"] = wsgi_conf["ssl.certfile"]
        options["keyfile"] = wsgi_conf["ssl.keyfile"]
    StandaloneApplication("src:app", options).run()


if __name__ == "__main__":
    entrypoint()
