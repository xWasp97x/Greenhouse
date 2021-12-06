import os.path
import yaml
from loguru import logger
from observer_pattern import Observer, Observable
from mqtt_subscriber import Subscriber
import pandas as pd
from datetime import datetime, timedelta, timezone
import parsers


class Thing(Observable):
    def __init__(self, data=None):
        super().__init__()
        self.data = None
        if data is not None:
            self.init_data(data)

    def init_data(self, data: pd.DataFrame):
        self.data = data

    def add_data(self, new_data: pd.DataFrame):
        self.data = pd.concat((self.data, new_data))
        self.notify_observers(new_data)


class Backend(Observer):
    def __init__(self, config_path='./config.yaml'):
        logger.debug('Initializing backend...')
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        self.subscriber = None
        self.init_subscriber()
        self.data = self.load_data(self.config['BACKEND']['data_path'])
        # self.data = {}
        self.PARSERS = {'sensors': parsers.CategoryParser,
                        'actuators': parsers.ActuatorsParser,
                        'controllers': parsers.ControllersParser}
        logger.debug('Backend ready.')

    @staticmethod
    def load_data(path) -> dict:
        logger.debug(f'Loading data from "{path}"...')
        categories = os.listdir(path)
        logger.debug(f'Categories found: {categories}')

        data = {}

        for category in categories:
            files = os.listdir(os.path.join(path, category))
            data[category] = {filename.replace('.csv', ''): Thing(pd.read_csv(os.path.join(path, category, filename)))
                              for
                              filename in files}

        logger.debug('Data loaded.')

        return data

    def update(self, payload: dict):
        logger.debug(f'New data received: {payload}')

        try:
            time = datetime.strptime(payload['datetime'], '%Y-%m-%d_%H-%M-%S').replace(tzinfo=timezone.utc)
        except TypeError as te:
            logger.error(f'Malformed json: {payload}; {te}')
            return

        if datetime.now(timezone.utc) - time > timedelta(minutes=30):
            logger.warning(f'Data dropped due to server <-> IoT device time difference')
            return

        payload.pop('datetime')

        sensor: str
        for category, values in payload.items():
            if category.lower() not in self.data:
                self.data[category] = dict()

            parser = self.PARSERS[category]()
            elements = parser.parse(category=values, time=time)

            for name, element in elements.items():
                if name not in self.data[category]:
                    self.data[category][name] = Thing(element)
                else:
                    self.data[category][name].add_data(element)

            self.save_dfs(self.data[category], category)

    def save_dfs(self, dfs: dict, sub_path: str = ''):
        thing: Thing
        for name, thing in dfs.items():
            self.save_df(thing, name, sub_path)

    def save_df(self, thing: Thing, name: str, sub_path: str = ''):
        root = self.config['BACKEND']['data_path']
        relative_path = os.path.join(root, sub_path)

        if not os.path.exists(relative_path):
            os.mkdir(relative_path)

        filepath = os.path.join(root, sub_path, f'{name}.csv')
        logger.debug(f'Saving {name} DataFrame to {filepath}...')
        thing.data.to_csv(filepath, columns=thing.data.columns, index=False)
        logger.debug(f'Saved.')

    def init_subscriber(self):
        logger.info(f'Setting up subscriber...')
        config = self.config['MQTT_BROKER']
        broker = config['address']
        port = config['port']
        qos = config['qos']
        topic = config['topic']
        mqtt_id = config['id']

        self.subscriber = Subscriber(broker, port, topic, qos, mqtt_id)
        self.subscriber.connect()
        self.subscriber.start()
        self.subscriber.add_observer(self)
        logger.success('Subscriber ready.')
