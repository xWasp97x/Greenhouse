import os.path
import yaml
from loguru import logger
from observer_pattern import Observer
from mqtt_subscriber import Subscriber
import sys
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import parsers

log_format = '<light-black>{time:YYYY-MM-DD HH:mm:ss.SSS}</light-black>' \
             ' <level>{name}.{function}@{line} | {level}: {message}</level>'


class Dashboard(Observer):
    def __init__(self, config_path='./config.yaml'):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        self.init_logger(self.config['LOGGER']['path'])
        self.subscriber = None
        self.init_subscriber()
        self.data = self.load_data(self.config['BACKEND']['data_path'])
        # self.data = {}
        st.title(self.config['FRONTEND']['title'])
        self.PARSERS = {'sensors': parsers.CategoryParser,
                        'actuators': parsers.ActuatorsParser,
                        'controllers': parsers.ControllersParser}

    @staticmethod
    def load_data(path) -> dict:
        logger.debug(f'Loading data from "{path}"...')
        categories = os.listdir(path)
        logger.debug(f'Categories found: {categories}')

        data = {}

        for category in categories:
            files = os.listdir(os.path.join(path, category))
            data[category] = {filename.replace('.csv', ''): pd.read_csv(os.path.join(path, category, filename)) for
                              filename in files}

        logger.debug('Data loaded.')

        return data

    def update(self, payload: dict):
        logger.debug(f'New data received: {payload}')

        timestamp = payload['timestamp']
        time = datetime.fromtimestamp(timestamp)

        if datetime.now() - time > timedelta(hours=5):
            logger.warning(f'Data dropped due to server <-> IoT device time difference')
            return

        payload.pop('timestamp')

        sensor: str
        for category, values in payload.items():
            if category.lower() not in self.data:
                self.data[category] = dict()

            parser = self.PARSERS[category]()
            elements = parser.parse(category=values, time=time)

            for name, element in elements.items():
                if name not in self.data[category]:
                    self.data[category][name] = element
                else:
                    self.data[category][name] = pd.concat([self.data[category][name], element])

            self.save_dfs(self.data[category], category)

    def save_dfs(self, dfs: dict, sub_path: str = ''):
        df: pd.DataFrame
        for name, df in dfs.items():
            self.save_df(df, name, sub_path)

    def save_df(self, df: pd.DataFrame, name: str, sub_path: str = ''):
        root = self.config['BACKEND']['data_path']
        relative_path = os.path.join(root, sub_path)

        if not os.path.exists(relative_path):
            os.mkdir(relative_path)

        filepath = os.path.join(root, sub_path, f'{name}.csv')
        logger.debug(f'Saving {name} DataFrame to {filepath}...')
        df.to_csv(filepath, columns=df.columns, index=False)
        logger.debug(f'Saved.')

    @staticmethod
    def init_logger(logs_path):
        logger.remove()
        logger.add(sys.stdout, format=log_format, colorize=True)
        logger.add(os.path.join(logs_path, '{time:YYYY-MM-DD}.log'), format=log_format,
                   colorize=False, compression='zip', rotation='00:00')

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


if __name__ == '__main__':
    dashboard = Dashboard()
    while True:
        pass
