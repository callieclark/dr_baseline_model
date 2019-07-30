import pandas as pd
import os, sys
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay
from sklearn.utils import check_array
import numpy as np
from datetime import timedelta
import pytz, datetime

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))+'/'

def mean_absolute_percentage_error(y_true, y_pred):
    mask = y_true != 0
    return (np.fabs(y_true - y_pred)/y_true)[mask].mean()

# function that returns a list of days not including weekends, holidays, or event day
# if pge == True will return weekdays for PG&E otherwise it will return weekdays for SCE
def get_workdays(start,end):
    start = pd.to_datetime(start).date()
    end = pd.to_datetime(end).date()
    us_bd = CustomBusinessDay(calendar=USFederalHolidayCalendar())
    workdays = pd.DatetimeIndex(start=start, end=end, freq=us_bd)
    return workdays

# Returns the start and end timestamp of a single day
def get_window_of_day(date):
    date = pd.to_datetime(date).date()
    start, end = pd.date_range(start=date, periods=2, freq='1d', tz='US/Pacific')
    # start_ts = start.isoformat()
    # end_ts = end.isoformat()
    start_ts = pytz.timezone("US/Pacific").localize(datetime.datetime(year=start.year, month=start.month, day=start.day, hour=start.hour, minute=0))
    end_ts = pytz.timezone("US/Pacific").localize(datetime.datetime(year=end.year, month=end.month, day=end.day, hour=end.hour, minute=0))
    return start_ts, end_ts

def get_closest_station(site):
    stations = pd.read_csv(os.path.join(PROJECT_ROOT, 'weather_stations.csv'), index_col='site')
    try:
        uuid = stations.loc[site].values[0]
        return uuid
    except:
        print("couldn't find closest weather station for %s" % site)
        return None

def get_date_str(date):
    date = pd.to_datetime(date).date()
    return format(date)

def get_month_window(date, time_delta=2):
    end_date = pd.to_datetime(date).date() + timedelta(days=time_delta)
    start_date = end_date - timedelta(days=30)
    # start_ts = pd.to_datetime(start_date).tz_localize('US/Pacific').isoformat()
    # end_ts = pd.to_datetime(end_date).tz_localize('US/Pacific').isoformat()
    start_ts = pytz.timezone("US/Pacific").localize(datetime.datetime(year=start_date.year, month=start_date.month, day=start_date.day, hour=0, minute=0))
    end_ts = pytz.timezone("US/Pacific").localize(datetime.datetime(year=end_date.year, month=end_date.month, day=end_date.day, hour=0, minute=0))

    return start_ts, end_ts
