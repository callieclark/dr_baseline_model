import pandas as pd
import datetime
from pandas.tseries.holiday import USFederalHolidayCalendar as calendar
from pandas.tseries.offsets import CustomBusinessDay

import numpy as np
import datetime,pytz
from numpy import trapz #only used in plot metric bars
#from Wrapper import *
from sklearn.metrics import mean_squared_error
from sklearn.utils import check_array
from sklearn.linear_model import RidgeCV
from scipy import special
from abc import ABC, abstractmethod

from .feature_engineering import create_ridge_features
from .utils import get_window_of_day, get_workdays, get_closest_station, get_month_window, get_twomonth_window
from .static_models import weather_model, power_model
from .get_data import get_df

class BaselineModel(ABC):

    @abstractmethod
    def train(self, site, exclude_dates):
        '''
        Train model on building data, from 2016-01-01 to today.
        Arguments:
            site (str): building site name
            exclude dates (list of datetime.date or string in YYYY-MM-DD format): dates to exclude from training
        '''
        pass

    @abstractmethod
    def predict(self, site, date):
        '''
        Arguments:
            site (str): building site name
            exclude dates (datetime.date or string in YYYY-MM-DD format): dates to predict on
        '''
        pass


class WeatherModel(BaselineModel):

    def __init__(self, init_args, rmse=None):
        '''
        init_args:
            0: Number of days before to choose
            1: Number of days before to search from
        '''
        self.X = init_args[0]
        self.Y = init_args[1]
        self.rmse = rmse
        self.name = "Weather Model: {} out of {} last days".format(self.X, self.Y)
        self.site = None
        self.exclude_dates = None

    def train(self, site, exclude_dates):
        self.site = site
        self.exclude_dates = exclude_dates
        return

    def predict(self, site, event_day):
        # Get the correct data for prediction
        start, end = get_twomonth_window(event_day)
        data = get_df(site, start, end, agg='MEAN', interval='15m')
        #added two lines below
        #data['weather'] = data['weather'].interpolate()
        event_weather=data[event_day.strftime("%Y-%m-%d")][['weather']]
        actual, prediction,baseline_weather = weather_model(event_day, data, self.exclude_dates, self.X, self.Y)
        return actual, prediction, event_weather, baseline_weather

class PowerModel(BaselineModel):

    def __init__(self, init_args, rmse=None):
        '''
        init_args:
            0: Number of days before to choose
            1: Number of days before to search from
        '''
        self.X = init_args[0]
        self.Y = init_args[1]
        self.rmse = rmse
        self.name = "Power Model: {} out of {} last days".format(self.X, self.Y)
        self.site = None
        self.exclude_dates = None

    def train(self, site, exclude_dates):
        self.site = site
        self.exclude_dates = exclude_dates
        return

    def predict(self, site, event_day):
        # Get the correct data for prediction
        start, end = get_month_window(event_day)
        data = get_df(site, start, end, agg='MEAN', interval='15m')
        #added two lines below
        #data['weather'] = data['weather'].interpolate()
        event_weather=data[event_day.strftime("%Y-%m-%d")][['weather']]

        actual, prediction, baseline_weather = power_model(event_day, data, self.exclude_dates, self.X, self.Y)
        return actual, prediction, event_weather, baseline_weather

class RidgeModel(BaselineModel):

    def __init__(self, rmse=None):
        self.model = None
        self.rmse = rmse
        self.name = "Ridge Model"
        self.site = None
        self.exclude_dates = None


    def train(self, site, exclude_dates):
        """
        Fit the regression model for a site during for the specified window
        exclude_dates is a an optional set of datetime.date objects to exclude from training
        cli: pymortar client
        """
        # start_train = pd.to_datetime('2016-01-01').tz_localize('US/Pacific').isoformat()
        # end_train = pd.to_datetime(datetime.datetime.today().date()).tz_localize('US/Pacific').isoformat()

        start_train = pytz.timezone("US/Pacific").localize(datetime.datetime(year=2016, month=1, day=1, hour=1, minute=0))
        end_train = pytz.timezone("US/Pacific").localize(datetime.datetime.today())
        alphas = [0.0001, .001, 0.01, 0.05, 0.1, 0.5, 1, 10]

        # Get data from pymortar
        data = get_df(site, start_train, end_train)

        # Get weekdays
        data['date'] = data.index.date
        weekdays = get_workdays(start_train, end_train)
        day_filter = [d in weekdays for d in data['date']]
        df = data[day_filter]

        # Exclude dates
        day_filter = [d not in exclude_dates for d in df.index.date]
        df = df[day_filter]

        # Create ridge features
        df = create_ridge_features(df)

        # Remove NA rows
        df = df.dropna()
        df = df[df['power'] != 0]

        # Train model
        X_train, y_train = df.drop(['power', 'weather', 'date'], axis=1), df['power']
        model = RidgeCV(normalize=True, alphas=alphas)
        model.fit(pd.DataFrame(X_train), y_train)

        # Train Error
        y_pred = model.predict(pd.DataFrame(X_train))
        self.model = model

    def predict(self, site, event_day):
        start, end = get_window_of_day(event_day)

        # Get data from pymortar
        #changed line below
        data = get_df(site, start, end, agg='MEAN', interval='15m')
        data['weather'] = data['weather'].interpolate()
        event_weather=data[event_day.strftime("%Y-%m-%d")][['weather']]

        # Get ridge features
        df = create_ridge_features(data)

        # Take away power from predicting data
        X_test, actual = df.drop(['power', 'weather'], axis=1), df['power']

        # Predict for the specified event date
        baseline = self.model.predict(X_test)
        baseline = pd.Series(baseline, index=actual.index)
        baseline_weather='N/A'

        return actual, baseline, event_weather, baseline_weather

all_models = {
    'weather_5_10': {
        'model_object': WeatherModel,
        'init_args': (5, 10)
    },
    'weather_10_10': {
        'model_object': WeatherModel,
        'init_args': (10, 10)
    },
    'weather_15_20': {
        'model_object': WeatherModel,
        'init_args': (15, 20)
    },
    'weather_20_20': {
        'model_object': WeatherModel,
        'init_args': (20, 20)
    },
    'power_3_10': {
        'model_object': PowerModel,
        'init_args': (3, 10)
    },
    'power_5_10': {
        'model_object': PowerModel,
        'init_args': (5, 10)
    },
    'power_10_10': {
        'model_object': PowerModel,
        'init_args': (10, 10)
    },
    'ridge': {
        'model_object': RidgeModel,
        'init_args': None
    }
}
