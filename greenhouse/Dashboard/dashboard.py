import os.path
import yaml
from loguru import logger
from observer_pattern import Observer
from mqtt_subscriber import Subscriber
import sys
import streamlit as st
import pandas as pd
from datetime import datetime

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
		st.title(self.config['FRONTEND']['title'])

	def load_data(self, path) -> dict:
		logger.debug(f'Loading data from "{path}"...')
		files = os.listdir(path)
		logger.debug(f'csvs found: {files}')

		data = {filename.replace('.csv', ''): pd.read_csv(os.path.join(path, filename)) for filename in files}
		logger.debug('Data loaded.')

		return data

	def update(self, payload: dict):
		logger.debug(f'New data received: {payload}')

		timestamp = payload['timestamp']
		payload.pop('timestamp')

		sensor: str
		for key, value in payload.items():
			if key.lower() not in self.data:
				self.data[key] = pd.DataFrame(columns=['datetime', 'value'])

			new_data = {'datetime': datetime.fromtimestamp(timestamp),
				 'value': value}

			self.data[key].append(new_data, ignore_index=True)
			self.save_df(self.data[key], key)

	def save_df(self, df: pd.DataFrame, name: str):
		filepath = os.path.join(self.config['BACKEND']['data_path'], f'{name}.csv')
		logger.debug(f'Saving {name} DataFrame to {filepath}...')
		df.to_csv(filepath, columns=df.columns)
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
