#!/usr/bin/env python

import numpy as np
import pandas as pd
import sqlite3

files = {"MSO_all":'../input/MSO_data.csv', "stops": '../input/stops.csv',
         "packages": '../input/packages.csv', "vehicles": '../input/vehicles.csv'}
delievery_date = "9/6/2018"

def convertTimestampToNumber(time):
    '''
    convert a time stamp in hh:mm:rr format to a four digit integer hhmm
    :param time:
    :return:
    '''
    time_list = time.split(":")
    time_no = int(time_list[0])*60 + int(time_list[1])

    return time_no

def readInput():
    '''
    read input data from files,
    :param filename:
    :return: dict with keys locations, time windows, suppliers, etc
    '''

    MSO_all = files["MSO_all"]
    dt_MSO_all = pd.read_csv(MSO_all)

    # below stops, packages and vehicles data are from Tim's toy example
    stops = files["stops"]  # import stops data
    dt_stops = pd.read_csv(stops)
    packages = files["packages"]
    dt_packages = pd.read_csv(packages)
    vehicles = files["vehicles"]
    dt_vehicles = pd.read_csv(vehicles)

    print("dt_MSO_all shape:", dt_MSO_all.shape)
    conn = sqlite3.connect('../input/vrptw.db')
    dt_MSO_all.to_sql("MSO_all", con=conn, if_exists="replace")
    dt_packages.to_sql("packages", con=conn, if_exists="replace")
    dt_stops.to_sql("stops", con=conn, if_exists="replace")
    dt_vehicles.to_sql("vehicles", con=conn, if_exists="replace")
    conn.close()

    output = {}
    dt_for_delivery = dt_MSO_all.loc[dt_MSO_all['Requested Delivery Date']
                                     == delievery_date, :] # select delivery for the date
    print("size of dt_for_delivery:", dt_for_delivery.shape)
    suppliers = dt_for_delivery[['supplier_company_code', 'Supplier Warehouse - Lat',
                                 'Supplier Warehouse - Long', 'pickup_hours_from', 'pickup_hours_to']].drop_duplicates(['supplier_company_code','Supplier Warehouse - Lat',
                                 'Supplier Warehouse - Long', 'pickup_hours_from', 'pickup_hours_to'])
    #print('unique suppliers:', suppliers)
    retailers = dt_for_delivery[['retailer_company_id', 'Retailer Location - Lat',
                                 'Retailer Location - Long', 'receiving_hours_from', 'receiving_hours_to']].drop_duplicates(['retailer_company_id', 'Retailer Location - Lat',
                                 'Retailer Location - Long', 'receiving_hours_from', 'receiving_hours_to'])
    supplier_retailer = dt_for_delivery[['supplier_company_code', 'retailer_company_id']].drop_duplicates(['supplier_company_code', 'retailer_company_id'])
    #print('unique suppliers retailer pair:', supplier_retailer)
    # populate locations (coordinates) for both suppliers and retailers
    demand_by_retailer = pd.pivot_table(dt_for_delivery, values=['Weight [kg]'], index=['retailer_company_id'],
                                        aggfunc=[np.sum])

    # print(demand_by_retailer.head(10))
    locations = list()
    supplier_lat = suppliers['Supplier Warehouse - Lat'].tolist()
    supplier_long = suppliers['Supplier Warehouse - Long'].tolist()
    for i in range(len(supplier_lat)):
        locations.append((supplier_lat[i], supplier_long[i]))

    retailer_lat = retailers['Retailer Location - Lat'].tolist()
    retailer_long = retailers['Retailer Location - Long'].tolist()
    for i in range(len(retailer_lat)):
        locations.append((retailer_lat[i], retailer_long[i]))
    output["locations"] = locations
    #print("output locations:", output["locations"])
    # populate time windows for both suppliers and retailers
    time_windows = list()
    supplier_from = suppliers['pickup_hours_from'].tolist()
    supplier_to = suppliers['pickup_hours_to'].tolist()
    supplier_from = [convertTimestampToNumber(i) for i in supplier_from]
    supplier_to = [convertTimestampToNumber(i) for i in supplier_to]
    for i in range(len(supplier_from)):
        time_windows.append((supplier_from[i], supplier_to[i]))

    retailer_from = retailers['receiving_hours_from'].tolist()
    retailer_to = retailers['receiving_hours_to'].tolist()
    retailer_from = [convertTimestampToNumber(i) for i in retailer_from]
    retailer_to = [convertTimestampToNumber(i) for i in retailer_to]
    for i in range(len(retailer_from)):
        time_windows.append((retailer_from[i], retailer_to[i]))
    output["time_windows"] = time_windows
    print("output time windows:", output["time_windows"])
    print("length of locations:", len(output["locations"]))
    print("length of time windows:", len(output["time_windows"]))
    return output

readInput()
#print(convertTimestampToNumber("16:20:00"))