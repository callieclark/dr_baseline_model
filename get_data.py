#import pymortar
import pandas as pd
import os
import numpy as np
import xbos_services_getter

from .utils import get_closest_station
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))+'/'
#cli = pymortar.Client()

outdoor_historic_stub=xbos_services_getter.get_outdoor_temperature_historic_stub()
meter_data_stub=xbos_services_getter.get_meter_data_historical_stub()


def get_weather(site, start, end, agg, window,stub=outdoor_historic_stub):
    OAT=xbos_services_getter.xbos_services_getter.get_raw_outdoor_temperature_historic(stub, site, start, end, window)
    return OAT[['temperature']]


def get_power(site, start, end, agg, window, stub=meter_data_stub):
    try:
        power_gb=xbos_services_getter.get_meter_data_historical(stub, site, start, end, point_type='Green_Button_Meter' , aggregate='MEAN', window= "15m")
        if site=='berkeley-corporate-yard': #need to fix this at microservice level
            power_gb=power_gb*4
        else:
            power_gb=power_gb*4000
        power_eagle=xbos_services_getter.get_meter_data_historical(stub, site, start, end, point_type='Building_Electric_Meter' , aggregate='MEAN', window= "15m")
        power=power_gb.fillna(value=power_eagle)
        #print("data for both")

    except:
        #todo make this more robust!!
        if site=="jesse-turner-center":
            power=xbos_services_getter.get_meter_data_historical(stub, site, start, end, point_type='Building_Electric_Meter' , aggregate='MEAN', window= "15m")
        else:
            power_gb=xbos_services_getter.get_meter_data_historical(stub, site, start, end, point_type='Green_Button_Meter' , aggregate='MEAN', window= "15m")
            if site=='berkeley-corporate-yard': #need to fix this at microservice level
                power_gb=power_gb*4
            else:
                power_gb=power_gb*4000
    return power #returned in watts

def get_df(site, start, end, agg='MEAN', interval='15m'):
    if site=='csu':
        data=pd.read_csv(os.path.join(PROJECT_ROOT, 'csu_data.csv'),index_col='ts')
    else:
    # Get weather
        weather = get_weather(site, start, end, agg=agg, window=interval)
        if weather.index.tz is None:
            weather.index = weather.index.tz_localize('UTC')
        weather.index = weather.index.tz_convert('US/Pacific')

        # closest_station = get_closest_station(site)
        # if closest_station is not None:
        #     weather = pd.DataFrame(weather[closest_station])
        # else:
        #     weather = pd.DataFrame(weather.mean(axis=1))
        # Get power
        power = get_power(site, start, end, agg=agg, window=interval)

        if power.index.tz is None:
            power.index = power.index.tz_localize('UTC')
        power.index = power.index.tz_convert('US/Pacific')

        # Merge
        #power_sum = pd.DataFrame(power.sum(axis=1))
        #data = power_sum.merge(weather, left_index=True, right_index=True)
        data = power.merge(weather, left_index=True, right_index=True)
        data.columns = ['power', 'weather'] #power in units of watts

    return data
