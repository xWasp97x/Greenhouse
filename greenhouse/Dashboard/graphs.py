from dash import dcc
from plotly.graph_objs import Scatter
import pandas as pd
import plotly.graph_objs as go
from backend import Thing
from observer_pattern import Observer
from threading import Lock


class SafeList:
    def __init__(self):
        self._data = []
        self.mutex = Lock()

    def append(self, value):
        self.mutex.acquire()
        self._data.append(value)
        self.mutex.release()

    @property
    def data(self) -> list:
        data = self._data
        return data

    def reset(self):
        self.mutex.acquire()
        self._data = []
        self.mutex.release()

    def empty(self) -> bool:
        return len(self._data) == 0


class LineGraph(dcc.Graph, Observer):
    def __init__(self, title: str, graph_id: str, thing: Thing, axes: tuple, y_title: str, x_title: str = ''):
        self.x_title = x_title
        self.y_title = y_title
        self.title = title
        self.axes = axes
        self.thing = thing
        self._temp = SafeList()  # Each element is: (x, y)

        self.thing.add_observer(self)

        self.type = 'lines'
        figure = {'layout': {'title': title,
                             'xaxis': {'title': x_title},
                             'yaxis': {'title': y_title}},
                  'data': [{'x': self.thing.data[axes[0]],
                            'y': self.thing.data[axes[1]],
                            'type': 'lines'}]}
        super().__init__(figure=figure, id=graph_id)

    def update(self, payload):
        self.add_data(payload)

    def _parse_data(self, new_data: pd.DataFrame) -> dict:
        return {'x': list(new_data[self.axes[0]]),
                'y': list(new_data[self.axes[1]])}

    @property
    def data(self):
        return self.thing.data

    def add_data(self, new_data: pd.DataFrame):
        parsed = self._parse_data(new_data)

        [self._temp.append((x, y)) for x, y in zip(parsed['x'], parsed['y'])]

    def get_figure(self) -> dict:
        figure = {'layout': {'title': self.title,
                             'xaxis': {'title': self.x_title},
                             'yaxis': {'title': self.y_title}},
                  'data': [{'x': self.data[self.axes[0]],
                            'y': self.data[self.axes[1]],
                            'type': self.type}]}

        return figure

    def get_scatter(self) -> Scatter:
        scatter = Scatter(x=self.data['x'],
                          y=self.data['y'],
                          name=self.title,
                          mode=self.type)
        return scatter

    def latest_data(self) -> dict:
        if self._temp.empty():
            return {'x': [],
                    'y': []}

        x_axes_data, y_axes_data = zip(*[e for e in self._temp.data])
        self._temp.reset()
        return {'x': x_axes_data,
                'y': y_axes_data}
