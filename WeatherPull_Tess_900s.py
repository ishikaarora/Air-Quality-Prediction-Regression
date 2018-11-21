from time import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# import pandasql as ps
import glob
from dateutil import parser
from datetime import timedelta, date
import requests
import json

mesowest_api_key = "KzxxYow297burLSv2E54TEQhhrx7NQCfWR7"

start_date = date(2016, 1, 1)
end_date = date(2016, 12, 31)

def get_counties():
    counties_abbrev = pd.read_csv("counties_abbrev_Tess_900s.csv")
    counties_abbrev.columns = ["OrigIndex", "State", "County", "Abbreviation"]
    counties_abbrev["County"] = counties_abbrev["County"].apply(lambda x: x.replace(" ", "%"))
    counties_abbrev["State"] = counties_abbrev["State"].apply(str.strip)
    counties_abbrev["County"] = counties_abbrev["County"].apply(str.strip)
    counties_abbrev["is_city"] = 0

    # counties_abbrev = counties_abbrev[counties_abbrev['County'] == 'Berkshire']
    return counties_abbrev

# Helper functions
def get_token(api_key):
    response = requests.get("https://api.mesowest.net/v2/auth?apikey=" + api_key)
    return json.loads(response.content.decode("latin1"))["TOKEN"]

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def get_avg_filt(dic, var):
    if isinstance(dic[var], dict):
        return dic[var]["average"]
    else:
        return np.nan

def get_avg(response, var):
    if "STATION" in response.keys():
        stations = response["STATION"]
        N = len(stations)
        if stations:
            return np.nanmean([get_avg_filt(y, var) for y in [x["STATISTICS"] for x in stations if "STATISTICS" in x.keys()] if var in y.keys()])
        else:
            return np.nan
    else:
        print("no STATION in keys")
        return np.nan
# @profile
def run_api_query(url):
    # t1 = time()
    response = requests.get(url)
    # t2 = time()
    resp_json = json.loads(response.text)
    # t3 = time()
    # print("Time for quering data from URL: {}".format(t2-t1))
    # print("Time for loading into json: {}".format(t3-t2))
    return resp_json
# @profile
def run_mesowest_api(state_abbrev, county, year, month, day, token):
    date1 = str(year) + str(month).zfill(2) + str(day).zfill(2)
    date2 = str(year) + str(month).zfill(2) + str(day).zfill(2)
    # is_city = counties_abbrev.loc[(counties_abbrev['County'] == county) & (counties_abbrev['Abbreviation'] == state_abbrev),"is_city"].values[0]
    # print(is_city)
    # if(is_city):
    #     print("This county is actually a city. Querying by city...")
    #     url = "http://api.mesowest.net/v2/stations/statistics?state=" + state_abbrev + "&city=" + county + "&start=" + date1 + "0000&end=" + date2 + "0000&obtimezone=local&token=" + token + "&type=average"
    #     print(url)
    # else:
    url = "http://api.mesowest.net/v2/stations/statistics?state=" + state_abbrev + "&county=" + county + "&start=" + date1 + "0000&end=" + date2 + "0000&obtimezone=local&token=" + token + "&type=average"
    # print(url)
    resp_json = run_api_query(url)

    # if "STATION" in resp_json.keys():
    #     if resp_json["STATION"]:
    #         pass
    #     else:
    #         counties_abbrev.loc[(counties_abbrev['County'] == county) & (counties_abbrev['Abbreviation'] == state_abbrev),"is_city"] = 1
    #         print("No data found by county. Querying by city...")
    #         print(counties_abbrev.loc[(counties_abbrev['County'] == county) & (counties_abbrev['Abbreviation'] == state_abbrev),"is_city"].values[0])
    #         url = "http://api.mesowest.net/v2/stations/statistics?state=" + state_abbrev + "&city=" + county + "&start=" + date1 + "0000&end=" + date2 + "0000&obtimezone=local&token=" + token + "&type=average"
    #         resp_json = run_api_query(url)

    return resp_json
# @profile
def get_county_weather_data(token, state, county, start_date, end_date, *argv):
    weather = dict()
    for arg in argv:
        weather[arg] = []

    dates = []
    # print("getting token")

    for dt in daterange(start_date, end_date):
        # t1 = time()
        response = run_mesowest_api(state, county, dt.year, dt.month, dt.day, token)
        dates.append(dt)
        for var in argv:
            weather[var] += [get_avg(response, var)]
        # t2 = time()
        # print("Finished pulling data for date {}. \nTime taken: {}".format(dt,t2-t1))

    weather_df = pd.DataFrame(weather)
    weather_df["Date"] = dates
    weather_df["State"] = state
    weather_df["County"] = county

    return weather_df
# @profile
def main():
    temp = pd.DataFrame()
    batch = 1
    counties_abbrev = get_counties()
    token = get_token(mesowest_api_key)

    for i in range(len(counties_abbrev)):
        county_name = counties_abbrev["County"][i]
        if isinstance(counties_abbrev["Abbreviation"][i], str) & isinstance(counties_abbrev["County"][i], str):
            print("\nGetting weather data for county {} - {}".format(counties_abbrev["OrigIndex"][i], county_name))
            # t1 = time()
            temp_upd = get_county_weather_data(token, counties_abbrev["Abbreviation"][i], counties_abbrev["County"][i].replace(" ", "%"), start_date, end_date, "air_temp_set_1", "altimeter_set_1", "wind_speed_set_1", "relative_humidity_set_1", "precip_accum_24_hour_set_1")
            temp = pd.concat([temp, temp_upd])
            # t2 = time()
            # print("Total time taken for county {} : {}".format(counties_abbrev["OrigIndex"][i], t2-t1))
        else:
            print("\nSkipping county {} - {}".format(i,county_name))
            continue

        # we don't want to write for just first county, write every 20 counties!
        if ((i!=0) & (i%10 == 0)):
            batch += 1
            temp.reset_index(drop=True,inplace=True)
            print("\nWriting data to csv for batch {}".format(batch))
            temp.to_csv("weather_data_Tess_900s_{}.csv".format(batch), index=None,header=True)
            temp = pd.DataFrame()

    batch += 1
    temp.reset_index(drop=True,inplace=True)
    print("\nWriting data to csv for batch {}".format(batch))
    temp.to_csv("weather_data_Tess_900s_{}.csv".format(batch), index=None,header=True)

if __name__ == "__main__":
    main()
