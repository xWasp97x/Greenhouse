import dash
from dash import dcc
from dash import html
from loguru import logger
import yaml
from backend import Backend


class Frontend:
    def __init__(self, backend: Backend, config_path='./config.yaml'):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)

        self.backend = Backend






if __name__ == "__main__":
    frontend = Frontend()
    frontend.app.run_server(debug=True)
