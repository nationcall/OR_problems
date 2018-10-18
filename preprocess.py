#!/usr/bin/env python

import numpy as np
import pandas as pd
import sqlite3

files = {"MSO_all":'../input/MSO_data.csv', "stops": '../input/stops.csv',
         "packages": '../input/packages.csv', "vehicles": '../input/vehicles.csv',
         "MrDonut_shop_detail":'../input/Mr_Donut_shop_detail.csv', "Mr_Donut_package":'../input/Mr_Donut_package.csv',
         "Mr_Donut_package2":'../input/Mr_Donut_package2.csv'}
delievery_date = "5/6/2018"
n_vehicle = 8

def convertTimestampToNumber(time):
    '''
    convert a time stamp in hh:mm:rr format to a four digit integer hhmm
    :param time:
    :return:
    '''
    time_list = time.split(":")
    time_no = int(time_list[0])*60 + int(time_list[1])

    return time_no

def readInputMSO():
    '''
    read input data from files, for multiple supplier optimization (MSO)
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
    print('length of suppliers retailer pair:', len(supplier_retailer))
    # populate locations (coordinates) for both suppliers and retailers
    demand_by_retailer = pd.pivot_table(dt_for_delivery, values=['Weight [kg]'], index=['retailer_company_id'],
                                        aggfunc=[np.sum])

    # print(demand_by_retailer.head(10))

    locations = list()
    supplier_lat = suppliers['Supplier Warehouse - Lat'].tolist()
    supplier_long = suppliers['Supplier Warehouse - Long'].tolist()
    locations.append((supplier_lat[0], supplier_long[0])) #intended for duplicate supplier as both depot and node
    k_times = n_vehicle
    for j in range(k_times): # add suppliers as both depot and nodes
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
    time_windows.append((supplier_from[0], supplier_to[0]))

    for j in range(k_times):
        for i in range(len(supplier_from)):
            time_windows.append((supplier_from[i], supplier_to[i]))

    retailer_from = retailers['receiving_hours_from'].tolist()
    retailer_to = retailers['receiving_hours_to'].tolist()
    retailer_from = [convertTimestampToNumber(i) for i in retailer_from]
    retailer_to = [convertTimestampToNumber(i) for i in retailer_to]


    for i in range(len(retailer_from)):
        time_windows.append((retailer_from[i], retailer_to[i]))
    output["time_windows"] = time_windows

    #add pick up and delivery precedence between supplier and retailer
    retailer_id = retailers['retailer_company_id'].tolist()
    supplier_name = suppliers['supplier_company_code'].tolist()
    print("supplier name:", supplier_name, "retailer_id:", retailer_id)
    pick_and_deliver = list()
    for spl_i in range(len(supplier_name)):
        spl_name = supplier_name[spl_i]
        its_retailer = supplier_retailer.loc[supplier_retailer['supplier_company_code'] == spl_name,
                                             'retailer_company_id'].tolist()
        if len(its_retailer) > 0:
            for retname in its_retailer:
                ret_i = retailer_id.index(retname)
                pick_and_deliver.append((spl_i+1, 1+ret_i+k_times*len(supplier_name)))


    output["pick_and_deliver"] = pick_and_deliver
    output["n_vehicle"] = n_vehicle
    output["n_supplier"] = len(supplier_name)
    #add retailer demands
    retailer_demand = list()
    for rid in retailer_id:
        agg_demand = demand_by_retailer.loc[rid].values[0]
        retailer_demand.append(agg_demand)
    output["retailer_demand"] = retailer_demand
    print("pick and deliver nodes pair:", pick_and_deliver)
    print("retailer demand:", retailer_demand)
    print("output time windows:", output["time_windows"])
    print("length of locations:", len(output["locations"]))
    print("length of time windows:", len(output["time_windows"]))
    output["names"] = list()
    return output

def readInputMSObyPackage():
    '''
    process and create nodes by packages, or supplier-retailer pair
    :return:
    '''
    output = {}
    MSO_all = files["MSO_all"]
    dt_MSO_all = pd.read_csv(MSO_all)

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
    dt_supplier_retailer = dt_for_delivery[['supplier_company_code', 'pickup_hours_from', 'pickup_hours_to', 'Supplier Warehouse - Lat', 'Supplier Warehouse - Long',
                                            'retailer_company_id', 'retailer_company_name', 'receiving_hours_from', 'receiving_hours_to', 'Retailer Location - Lat', 'Retailer Location - Long',
                                            'Weight [kg]']]
    supplier_retailer = dt_supplier_retailer.drop_duplicates(['supplier_company_code', 'retailer_company_id'])
    demand_by_retailer = pd.pivot_table(dt_supplier_retailer, values=['Weight [kg]'], index=['supplier_company_code', 'retailer_company_id'],
                                        aggfunc=[np.sum])
    demand_by_retailer.reset_index(inplace=True)
    demand_by_retailer.columns = ['supplier_company_code', 'retailer_company_id', 'weight']
    dt_supplier_retailer = pd.merge(supplier_retailer, demand_by_retailer, 'inner', left_on=['supplier_company_code', 'retailer_company_id'],
                                    right_on=['supplier_company_code', 'retailer_company_id'])
    print(dt_supplier_retailer.columns)
    print(dt_supplier_retailer.shape)
    #supplier_retailer = dt_for_delivery[['supplier_company_code', 'retailer_company_id', 'Weight [kg]']].drop_duplicates(['supplier_company_code', 'retailer_company_id'])
    #print('unique suppliers retailer pair:', supplier_retailer)
    #print('length of suppliers retailer pair:', len(supplier_retailer))
    # populate locations (coordinates) for both suppliers and retailers
    locations = list()
    time_windows = list()
    pick_and_deliver = list()
    demands = list()
    retail_demand = list()
    stops = list()
    for ind in range(dt_supplier_retailer.shape[0]):
        #print("ind:",ind)
        #print(dt_supplier_retailer.iloc[ind])
        locations.append(list(dt_supplier_retailer.iloc[ind][['Supplier Warehouse - Lat', 'Supplier Warehouse - Long']]))
        locations.append(list(dt_supplier_retailer.iloc[ind][['Retailer Location - Lat', 'Retailer Location - Long']]))
        windws = list(dt_supplier_retailer.iloc[ind][['pickup_hours_from', 'pickup_hours_to']])
        windws = [convertTimestampToNumber(i) for i in windws]
        time_windows.append(windws)
        windws = list(dt_supplier_retailer.iloc[ind][['receiving_hours_from', 'receiving_hours_to']])
        windws = [convertTimestampToNumber(i) for i in windws]
        time_windows.append(windws)
        stops.append(dt_supplier_retailer.iloc[ind]['supplier_company_code'])
        stops.append(dt_supplier_retailer.iloc[ind]['retailer_company_name'])
        retail_demand.append(-dt_supplier_retailer.iloc[ind]['weight'])
        retail_demand.append(dt_supplier_retailer.iloc[ind]['weight'])
        demands.append(0)
        demands.append(dt_supplier_retailer.iloc[ind]['weight'])
        pick_and_deliver.append((2*ind+1, 2*ind+1+1))
    locations.insert(0, [0, 0])
    time_windows.insert(0, [0, 1440])
    output["locations"] = locations
    output["time_windows"] = time_windows
    output["retailer_demand"] = retail_demand
    output["demands"] = demands
    output["n_supplier"] = len(suppliers)
    output["n_vehicle"] = n_vehicle
    output["pick_and_deliver"] = pick_and_deliver
    output["stops"] = stops

    print("pick and deliver nodes pair:", pick_and_deliver)
    print("retailer demand:", demands)
    print("output time windows:", output["time_windows"])
    print("locations:", output["locations"])
    print("length of locations:", len(output["locations"]))
    print("length of time windows:", len(output["time_windows"]))
    print("stops:", stops)
    return output


def readInputSSO():
    '''
    read input and process for single supplier optimization (SSO), for Mr Donut case
    :return:
    '''
    Mr_Donut_shop_dtail = files["MrDonut_shop_detail"]
    shop_detail = pd.read_csv(Mr_Donut_shop_dtail)
    Mr_Donut_package = files["Mr_Donut_package"]
    Mr_Donut_package2 = files["Mr_Donut_package2"]
    package_detail1 = pd.read_csv(Mr_Donut_package)
    package_detail2 = pd.read_csv(Mr_Donut_package2) #contains time windows
    package_detail2 = package_detail2.loc[package_detail2["DATE"] == "1-May", ["SHOP NAME", "FROM", "TO"]]
    package_detail = pd.merge(package_detail1, package_detail2, left_on=["deliver_to"], right_on=["SHOP NAME"])
    package_detail_join_shop_detail = pd.merge(package_detail, shop_detail, "inner", left_on=["deliver_to"],
                                               right_on=["SHOP NAME"])
    conn = sqlite3.connect('../input/vrptw.db')
    package_detail.to_sql("Mr_Donut_package_detail", con=conn, if_exists="replace")
    shop_detail.to_sql("Mr_Donut_shop_detail", con=conn, if_exists="replace")
    package_detail_join_shop_detail.to_sql("Mr_Donut_package_detail_join_shop_detail", con=conn, if_exists="replace")
    conn.close()

    output = {}
    suppliers = pd.DataFrame({"supplier name":["MISTER DONUT MANGGAHAN PLANT"], "supplier_lat":[14.602171],
                              "supplier_long":[121.093135],"supplier_from":['00:00'], "supplier_to":['23:59']})
    retailers = package_detail_join_shop_detail[["deliver_to", "LATITUDE", "LONGITUDE", "FROM", "TO"]]

    stops = list()
    supplier = suppliers['supplier name'].tolist()
    retailer = retailers['deliver_to'].tolist()
    for i in supplier:
        stops.append(i)
    for i in retailer:
        stops.append(i)
    output["stops"] = stops
    locations = list()
    supplier_lat = suppliers['supplier_lat'].tolist()
    supplier_long = suppliers['supplier_long'].tolist()
    #locations.append((supplier_lat[0], supplier_long[0])) #intended for duplicate supplier as both depot and node
    for i in range(len(supplier_lat)):
        locations.append((supplier_lat[i], supplier_long[i]))

    retailer_lat = retailers['LATITUDE'].tolist()
    retailer_long = retailers['LONGITUDE'].tolist()
    for i in range(len(retailer_lat)):
        locations.append((retailer_lat[i], retailer_long[i]))
    output["locations"] = locations

    # populate time windows for both suppliers and retailers
    time_windows = list()
    supplier_from = suppliers['supplier_from'].tolist()
    supplier_to = suppliers['supplier_to'].tolist()
    supplier_from = [convertTimestampToNumber(i) for i in supplier_from]
    supplier_to = [convertTimestampToNumber(i) for i in supplier_to]
    #time_windows.append((supplier_from[0], supplier_to[0]))

    for i in range(len(supplier_from)):
        time_windows.append((supplier_from[i], supplier_to[i]))

    retailer_from = retailers['FROM'].tolist()
    retailer_to = retailers['TO'].tolist()
    retailer_from = [convertTimestampToNumber(i) for i in retailer_from]
    retailer_to = [convertTimestampToNumber(i) for i in retailer_to]

    for i in range(len(retailer_from)):
        time_windows.append((retailer_from[i], retailer_to[i]))
    output["time_windows"] = time_windows

    retailer_demand = package_detail_join_shop_detail["weight"].tolist()

    output["retailer_demand"] = retailer_demand
    output["n_vehicle"] = 50
    print("length of time_windows:", len(time_windows), "first 5 elements:", time_windows[:5])
    print("length of locations:", len(locations), "first 5 elements:", locations[:5])
    print("length of demand:", len(retailer_demand), "first 5 elements:", retailer_demand[:5])
    print("length of stops:", len(stops))
    return output

#readInputMSO()
#readInputSSO()
#readInputMSObyPackage()
#print(convertTimestampToNumber("16:20:00"))