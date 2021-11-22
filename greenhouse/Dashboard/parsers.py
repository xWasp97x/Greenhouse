import pandas as pd
from datetime import datetime


class CategoryParser:
    def parse(self, category: dict, time=None) -> dict:
        if time is None:
            time = datetime.now()

        elements = dict()

        for element, value in category.items():
            df = self.get_df(value, time)
            elements[element] = df

        return elements

    @staticmethod
    def get_df(value, time: datetime) -> pd.DataFrame:
        return pd.DataFrame.from_dict({'datetime': [time], 'value': [value]})


class ActuatorsParser (CategoryParser):
    @staticmethod
    def get_df(value, time: datetime) -> pd.DataFrame:
        return pd.DataFrame.from_dict({'datetime': [time],
                                       'available': [value['available']]})


class ControllersParser (CategoryParser):
    @staticmethod
    def get_df(value, time: datetime) -> pd.DataFrame:
        return pd.DataFrame.from_dict({'datetime': [time],
                                       'enabled': [value['enabled']],
                                       'busy': [value['busy']]})

