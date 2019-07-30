import xbos_services_getter
from .utils import  get_month_window
from .get_greenbutton_id import *
import datetime as dtime
from datetime import timedelta
from .get_data import get_df
import numpy as np
import pandas as pd
import math
import os

# calculator = CostCalculator()
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))+'/'

price_stub=xbos_services_getter.xbos_services_getter.get_price_stub()

def eval_nan(x):
    if (not type(x) == str) and math.isnan(x):
        return None
    return x

def calc_price(power_vector, site, start_datetime, end_datetime):
    total_price = calc_total_price(power_vector, start_datetime, end_datetime, site)
    return total_price

def calc_total_price(power_vector,  start_datetime, end_datetime, site, interval='15min'):
    '''
    returns the total energy cost of power consumption over the given window
    the granularity is determined from the length of the vector and the time window
    TODO: Demand charges

    power_vector: a pandas series of power consumption (kW) over the given window

    start_datetime: the datetime object representing the start time (starts )
    end_datetime: the datetime object representing the start time
    '''

    time_delta = end_datetime - start_datetime
    interval_15_min = (3600*24*time_delta.days + time_delta.seconds)/(60*15)
    if len(power_vector) == interval_15_min or interval == '15min':
        energy_vector = power_15min_to_hourly_energy(power_vector)
        energy_vector.index = pd.date_range(start=start_datetime, end=end_datetime, freq='1h')
    else:
        energy_vector = power_vector
    #print("energy vector 1", energy_vector)
    energy_vector = energy_vector / 1000
    energy_prices=xbos_services_getter.xbos_services_getter.get_price(price_stub, site, 'ENERGY', start_datetime, end_datetime+timedelta(hours=1), window='1h')
    energy_prices=energy_prices.tz_convert('UTC')
    energy_prices=energy_prices.tz_localize(None)
    cost=energy_prices['price']*energy_vector
    total_cost=cost.sum()

    demand_prices=xbos_services_getter.xbos_services_getter.get_price(price_stub, site, 'DEMAND', start_datetime, end_datetime+timedelta(hours=1), window='1h')
    # can use this to figure out demand costs
    #energy is off by a factor of 1000 somewhere doe berkeley corp yard

    # ##demand price increase not yet implemented
    # # month_prior_start, month_prior_end = get_month_window(start_datetime.date(),time_delta=0)
    # # month_prior_energy=get_df(site, month_prior_start, month_prior_end)
    # # print('month energy', month_prior_energy['power'].max()) #check units
    # # print('pdp energy', power_vector.max()) #check units
    # #
    # # if power_vector.max() > month_prior_energy['power'].max():
    # #     increased_demand=power_vector.max()-month_prior_energy['power'].max()
    # #     demand_charge=increased_demand*demandPrices
    # #     print(demand_charge)

    return total_cost

def power_15min_to_hourly_energy(power_vector):
    energy_kwh = np.array(power_vector / 4.0) #TODO: Array or time-index series?
    result = pd.Series(np.sum(energy_kwh.reshape(-1, 4), axis=1))
    return result
