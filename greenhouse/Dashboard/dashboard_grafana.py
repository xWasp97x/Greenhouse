import pandas as pd
import yaml
from backend import Backend
import sys
import os
from loguru import logger
from backend import Thing
from observer_pattern import Observer
from sqlalchemy import create_engine
from time import sleep

log_format = '<light-black>{time:YYYY-MM-DD HH:mm:ss.SSS}</light-black>' \
             ' <level>{name}.{function}@{line} | {level}: {message}</level>'


class DBUpdater(Observer):
    def __init__(self, schema: str, table: str, thing: Thing, conn):
        self.schema = schema
        self.table_name = table
        thing.add_observer(self)
        self.conn = conn

    def update(self, payload):
        payload: pd.DataFrame
        payload.to_sql(name=self.table_name,
                       schema=self.schema,
                       con=self.conn,
                       if_exists='append')


class Dashboard:
    def __init__(self, config_path='./config.yaml'):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        self.backend = Backend(config_path)
        self.init_logger(self.config['LOGGER']['path'])
        self.db_engine = self.init_db_engine()
        self.db_connection = self.init_db_connection()
        self.updaters = self.init_updaters()

    def init_logger(self, logs_path):
        logger.remove()
        logger.add(sys.stdout, format=log_format, colorize=True, level=self.config['LOGGER']['level'])
        logger.add(os.path.join(logs_path, '{time:YYYY-MM-DD}.log'), format=log_format,
                   colorize=False, compression='zip', rotation='00:00')

    def init_db_engine(self):
        db_config = self.config['DATABASE']
        connection_string = f'postgresql+psycopg2://{db_config["user"]}:{db_config["password"]}@' \
                            f'{db_config["host"]}:5432/{db_config["database"]}'
        engine = create_engine(connection_string, isolation_level='SERIALIZABLE')
        return engine

    @logger.catch
    def init_db_connection(self):
        conn = self.db_engine.connect()
        return conn

    def init_updaters(self):
        data = self.backend.data
        sensors = data.get('sensors', {})
        updaters = [DBUpdater('data', 'temp_in', sensors.get('temp_in', Thing()), self.db_connection),
                    DBUpdater('data', 'moisture', sensors.get('MoistureReader', Thing()), self.db_connection)]

        return updaters


if __name__ == '__main__':
    dashboard = Dashboard(os.environ['config_file'])

    while True:
        sleep(60)
