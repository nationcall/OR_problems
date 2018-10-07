import math
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
from TSP_metaheuristic import getInputData

scaleup = 10
def euclid_distance(x1, y1, x2, y2):
  # Euclidean distance between points.
	dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
	return round(dist,2)
  
def create_distance_matrix(locations):
# Create the distance matrix.
	size = len(locations)
	dist_matrix = {}
	for from_node in range(size):
		dist_matrix[from_node] = {}
		for to_node in range(size):
			x1 = locations[from_node][0]
			y1 = locations[from_node][1]
			x2 = locations[to_node][0]
			y2 = locations[to_node][1]
			dist_matrix[from_node][to_node] = euclid_distance(x1, y1, x2, y2)
	#print(dist_matrix)
	return dist_matrix
  
def create_distance_callback(dist_matrix):
  # Create the distance callback.
	def distance_callback(from_node, to_node):
		return int(dist_matrix[from_node][to_node])

	return distance_callback

def create_data_array(inputdata):
	#process input data in list of points
	dt_inputs = inputdata.split('\n')
	#print("length of input:",len(dt_inputs))
	n_points = int(dt_inputs[0])
	#print("number of points:",n_points)
	points = []
	for pp in range(1,n_points+1):
		parts = dt_inputs[pp].split()
		points.append([float(parts[0])*scaleup,float(parts[1])*scaleup])
	return points

def cp_solver(inputdata):
	# Create the data.
	locations = create_data_array(inputdata)
	dist_matrix = create_distance_matrix(locations)
	dist_callback = create_distance_callback(dist_matrix)
	#print("dist_callback[0][1]:",dist_callback(0,1))
	tsp_size = len(locations)
	num_routes = 1
	depot = 0
	solution = []
	# Create routing model.
	if tsp_size > 0:
		routing = pywrapcp.RoutingModel(tsp_size, num_routes, depot)
		search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()
		routing.SetArcCostEvaluatorOfAllVehicles(dist_callback)
		# Solve the problem.
		assignment = routing.SolveWithParameters(search_parameters)
		if assignment:
			# Solution cost.
			print("Total distance: " + str(assignment.ObjectiveValue()/scaleup) + "\n")
			# Inspect solution.
			# Only one route here; otherwise iterate from 0 to routing.vehicles() - 1.
			route_number = 0
			node = routing.Start(route_number)
			start_node = node
			route = ''

			while not routing.IsEnd(node):
				route += str(node) + ' -> '
				solution.append(node)
				node = assignment.Value(routing.NextVar(node))
			route += '0'
			solution.append(0)
			print("Route:\n\n" + route)
			dist = 0
			for i in range(len(solution)-1):
				pp = dist_callback(solution[i],solution[i+1])
				#print("point",solution[i]," and point ",solution[i+1],pp)
				dist += dist_callback(solution[i],solution[i+1])
			#print("calculated dist:",dist)
		else:
			print('No solution found.')
	else:
		print('Specify an instance greater than 0.')
	return solution[:-1]


