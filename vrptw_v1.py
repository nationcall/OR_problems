#!/usr/bin/env python
import numpy as np
import pandas as pd
from math import *
from src.preprocess import readInputSSO
import time
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2

'''
Capacitated VRP with time windows
'''

def calculateFromCoordinates(point1, point2):
    '''
    calculate distance between two points in latitude and longitude
    :param point1: 
    :param point2: 
    :return: 
    '''
    lat1 = radians(point1[0])
    lon1 = radians(point1[1])
    lat2 = radians(point2[0])
    lon2 = radians(point2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    R = 6373 # radius of earth 6373 km
    a = pow(sin(dlat / 2), 2) + cos(lat1) * cos(lat2) * pow(sin(dlon / 2), 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    d = R * c
    return d


def create_data_model():
    '''
    store the data for the problem in dict data:
    1. get location coordinates
    :return:
    '''

    input = readInputSSO()
    data = {}
    data["locations"] = input["locations"]
    data["num_locations"] = len(data["locations"])
    data["time_windows"] = input["time_windows"]
    data["num_suppliers"] = 1
    data["retailer_demand"] = [0] + input["retailer_demand"]
    data["demands"] = data["retailer_demand"] #create transit node for each supplier and vehicle
    data["time_per_demand_unit"] = 0.5  # 5 minutes/unit
    data["num_vehicles"] = input["n_vehicle"]
    data["vehicle_capacity"] = 200
    data["vehicle_speed"] = 15/60  # Travel speed: 15km/h convert to m/min
    data["stops"] = input["stops"]
    #data["depot"] = ((0,1),(0,1),(0,1),(0,1))
    #data["depot"] = [(0,0,0,0),(1,1,1,1)]
    data["depot"] = 0
    #data["pick_and_deliver"] = input["pick_and_deliver"]
    return data

def deriveDistance(point1, point2):
    '''
    derive the distance matrix, either using Eucledian distance or Google API
    :return: distance matrix
    '''

    return calculateFromCoordinates(point1, point2)

def create_distance_evaluator(data):
    """Creates callback to return distance between points."""
    _distances = {}
    # precompute distance between location to have distance callback in O(1)
    for from_node in range(data["num_locations"]):
        _distances[from_node] = {}
        for to_node in range(data["num_locations"]):
            if from_node == to_node:
                _distances[from_node][to_node] = 0
            else:
                _distances[from_node][to_node] = deriveDistance(data["locations"][from_node], data["locations"][to_node])

    def distance_evaluator(from_node, to_node):
        """Returns the calculated distance between the two nodes"""
        return _distances[from_node][to_node]

    return distance_evaluator

def create_demand_evaluator(data):
    """Creates callback to get demands at each location."""
    _demands = data["demands"]

    def demand_evaluator(from_node, to_node):
        """Returns the demand of the current node"""
        del to_node
        return _demands[from_node]

    return demand_evaluator

def add_capacity_constraints(routing, data, demand_evaluator):
    """Adds capacity constraint"""
    capacity = 'Capacity'
    routing.AddDimension(
      demand_evaluator,
      0,  # null capacity slack
      data["vehicle_capacity"],
      True,  # start cumul to zero
      capacity)

def create_time_evaluator(data):
    """Creates callback to get total times between locations."""
    def service_time(data, node):
        """Gets the service time for the specified location."""
        return 5

    def travel_time(data, from_node, to_node):
        """Gets the travel times between two locations."""
        if from_node == to_node:
            travel_time = 0
        else:
            travel_time = deriveDistance(
                data["locations"][from_node],
                data["locations"][to_node]) / data["vehicle_speed"]
        return travel_time

    _total_time = {}
    # precompute total time to have time callback in O(1)
    for from_node in range(data["num_locations"]):
        _total_time[from_node] = {}
        for to_node in range(data["num_locations"]):
            if from_node == to_node:
                _total_time[from_node][to_node] = 0
            else:
                #_total_time[from_node][to_node] = int(travel_time(data, from_node, to_node))
                _total_time[from_node][to_node] = int(
                service_time(data, from_node) +
                travel_time(data, from_node, to_node))

    def time_evaluator(from_node, to_node):
        """Returns the total time between the two nodes"""
        return _total_time[from_node][to_node]

    return time_evaluator

def add_time_window_constraints(routing, data, time_evaluator):
    """Add Global Span constraint"""
    time = "Time"
    horizon = 60
    horizon1 = 1100
    routing.AddDimension(
      time_evaluator,
      horizon,  # allow waiting time
      horizon1,  # maximum time per vehicle
      False,  # don't force start cumul to zero since we are giving TW to start nodes
      time)
    time_dimension = routing.GetDimensionOrDie(time)
    # Add time window constraints for each location except depot
    # and "copy" the slack var in the solution object (aka Assignment) to print it
    for location_idx, time_window in enumerate(data["time_windows"]):
        #if location_idx in data["depot"][0] or location_idx in data["depot"][1]:
        if location_idx == data["depot"]:
            continue
        index = routing.NodeToIndex(location_idx)
        #print("time windows:", time_window[0], time_window[1])
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
        routing.AddToAssignment(time_dimension.SlackVar(index))
        # Add time window constraints for each vehicle start node
        # and "copy" the slack var in the solution object (aka Assignment) to print it
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        time_dimension.CumulVar(index).SetRange(data["time_windows"][0][0],
                                                data["time_windows"][0][1])
        routing.AddToAssignment(time_dimension.SlackVar(index))
    # Warning: Slack var is not defined for vehicle's end node
    #routing.AddToAssignment(time_dimension.SlackVar(self.routing.End(vehicle_id)))

###########
# Printer #
###########
def print_solution(data, routing, assignment): # pylint:disable=too-many-locals
    """Prints assignment on console"""
    print('Objective: {}'.format(assignment.ObjectiveValue()))
    total_distance = 0
    total_load = 0
    total_time = 0
    capacity_dimension = routing.GetDimensionOrDie('Capacity')
    time_dimension = routing.GetDimensionOrDie('Time')
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        distance = 0
        while not routing.IsEnd(index):
            load_var = capacity_dimension.CumulVar(index)
            time_var = time_dimension.CumulVar(index)
            slack_var = time_dimension.SlackVar(index)
            plan_output += ' {0} Load ({1}) Time({2},{3}) Slack({4},{5}) ->'.format(
                routing.IndexToNode(index),
                assignment.Value(load_var),
                assignment.Min(time_var),
                assignment.Max(time_var),
                assignment.Min(slack_var),
                assignment.Max(slack_var))
            previous_index = index
            index = assignment.Value(routing.NextVar(index))
            distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        load_var = capacity_dimension.CumulVar(index)
        time_var = time_dimension.CumulVar(index)
        slack_var = time_dimension.SlackVar(index)
        plan_output += ' {0} Load ({1}) Time({2},{3})\n'.format(
            routing.IndexToNode(index),
            assignment.Value(load_var),
            assignment.Min(time_var),
            assignment.Max(time_var))
        plan_output += 'Distance of the route: {0}m\n'.format(distance)
        plan_output += 'Load of the route: {}\n'.format(assignment.Value(load_var))
        plan_output += 'Time of the route: {}\n'.format(assignment.Value(time_var))
        print(plan_output)
        total_distance += distance
        total_load += assignment.Value(load_var)
        total_time += assignment.Value(time_var)
    print('Total Distance of all routes: {0}m'.format(total_distance))
    print('Total Load of all routes: {}'.format(total_load))
    print('Total Time of all routes: {0}min'.format(total_time))

def output_plan_result(data, routing, assignment):
    cols = ["vehicle", "stop_id", "lat", "lng", "arrive_after", "ordering", "stop_type", "delivery_weight",
            "pickup_weight", "delivery_volume", "pickup_volume", "arrive_before", "service_time", "return_after",
            "return_before", "parcel_origin", "carry_weight", "carry_volume", "leg_distance", "leg_time", "arrival_time"]
    capacity_dimension = routing.GetDimensionOrDie('Capacity')
    time_dimension = routing.GetDimensionOrDie('Time')
    output = pd.DataFrame()
    v_count = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        next_index = assignment.Value(routing.NextVar(index))
        if routing.IndexToNode(next_index) != 0:
            ct = 0
            v_count += 1
            carry_weight = 0
            while not routing.IsEnd(index):
                ct += 1
                current_vehicle = "vehicle"+str(v_count)
                iiindex = routing.IndexToNode(index)
                next_index = assignment.Value(routing.NextVar(index))
                #print("indexxx:", iiindex)
                stop_id = data["stops"][iiindex]
                lat = data["locations"][iiindex][0]
                lng = data["locations"][iiindex][1]
                arrive_after = data["time_windows"][iiindex][0]
                arrive_after = str(arrive_after // 60) + ":" + str(arrive_after - arrive_after // 60 * 60)
                arrive_before = data["time_windows"][iiindex][1]
                arrive_before = str(arrive_before // 60) + ":" + str(arrive_before - arrive_before // 60 * 60)
                ordering = ct
                stop_type = "pickup" if data["retailer_demand"][iiindex] == 0 else "deliver"
                delivery_weight = data["retailer_demand"][iiindex]
                pickup_weight = 0
                delivery_volume = delivery_weight
                pickup_volume = 0
                service_time = 5
                return_after = data["time_windows"][iiindex][0] if iiindex == 0 else ''
                return_before = data["time_windows"][iiindex][1] if iiindex == 0 else ''
                parcel_origin = data["stops"][0]
                carry_weight = assignment.Value(capacity_dimension.CumulVar(index))
                carry_volume = carry_weight
                leg_distance = routing.GetArcCostForVehicle(index, next_index, vehicle_id)
                leg_time = assignment.Value(time_dimension.CumulVar(next_index)) - assignment.Value(time_dimension.CumulVar(index))
                arrival_time = assignment.Value(time_dimension.CumulVar(index))
                arrival_time = str(arrival_time//60)+":"+str(arrival_time-arrival_time//60*60)
                dt = pd.DataFrame(data=[[current_vehicle, stop_id, lat, lng, arrive_after, ordering, stop_type,
                                          delivery_weight, pickup_weight, delivery_volume, pickup_volume, arrive_before,
                                          service_time, return_after, return_before, parcel_origin, carry_weight,
                                        carry_volume, leg_distance, leg_time, arrival_time]])
                #print(dt)
                index = assignment.Value(routing.NextVar(index))
                output = output.append(dt)
    output.columns = cols
    output.to_csv("../output/plan_result.csv")
    return

def plot_vehicle_route():
    return

def main():
    """Entry point of the program"""
    start = time.time()
    # Instantiate the data problem.
    data = create_data_model()
    #for i in range(data["num_locations"]):
    #    for j in range(data["num_locations"]):
    #        dist = travelTime(i, j)
    #        print(dist, end=' ')
    #    print('\n')
    # Create Routing Model
    routing = pywrapcp.RoutingModel(
        data["num_locations"],
        data["num_vehicles"],
        data["depot"])
    # Define weight of each edge
    distance_evaluator = create_distance_evaluator(data)
    routing.SetArcCostEvaluatorOfAllVehicles(distance_evaluator)
    # Add Capacity constraint
    demand_evaluator = create_demand_evaluator(data)
    add_capacity_constraints(routing, data, demand_evaluator)
    # Add Time Window constraint
    time_evaluator = create_time_evaluator(data)
    add_time_window_constraints(routing, data, time_evaluator)
    # Add Pickup and Delivery constraints

    # Setting first solution heuristic (cheapest addition).
    search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()
    search_parameters.time_limit_ms = 3000000
    #search_parameters.local_search_metaheuristic = (
    #    routing_enums_pb2.LocalSearchMetaheuristic.PATH_CHEAPEST_ARC)
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)  # pylint: disable=no-member
    # Solve the problem. PATH_CHEAPEST_ARC, PARALLEL_CHEAPEST_INSERTION
    assignment = routing.SolveWithParameters(search_parameters)
    print_solution(data, routing, assignment)
    output_plan_result(data, routing, assignment)
    end = time.time()
    print("Total run time:", end-start)


if __name__ == '__main__':
    main()

#point1 = (14.602414, 121.096511)
#point2 = (14.637756, 120.983021)
#print(calculateFromCoordinates(point1, point2))