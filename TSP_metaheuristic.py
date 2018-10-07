# TSP problem using metaheuristics
import math
from collections import namedtuple

Point = namedtuple("Point", ['x', 'y'])

def length(point1, point2):
	ak= math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
	return round(ak,2)

M = 100000
dm = [[0,12,10,M,M,M,12],[12,0,8,12,M,M,M],[10,8,0,11,3,M,9],
[M,12,11,0,11,10,M],[M,M,3,11,0,6,7],[M,M,M,10,6,0,9],[12,M,9,M,7,9,0]]
tabu_list = list()

#input data
def getInputData(inputdata):
	#process input data in list of points
	dt_inputs = inputdata.split('\n')
	#print("length of input:",len(dt_inputs))
	n_points = int(dt_inputs[0])
	#print("number of points:",n_points)
	points = []
	for pp in range(1,n_points+1):
		parts = dt_inputs[pp].split()
		points.append((float(parts[0]),float(parts[1])))
	dist_matrix = []
	for i in range(n_points):
		dist_i = []
		for j in range(n_points):
			dist_i.append(length(points[i],points[j]))
		dist_matrix.append(dist_i)
	#print("length of dist_matrix:",len(dist_matrix))
	#print("dist_matrix[0]:",dist_matrix[0])
	
	return [n_points,dist_matrix]
	
def initGreedySolution(route0):
	#generate a greedy solution 
	return
	
def deriveCost(route, dist_matrix=dm):
	#compute the cost for a travel route, given the distance matrix of nodes
	route_cost = 0
	for i in range(len(route)-1):
		route_cost += dist_matrix[route[i]-1][route[i+1]-1]
	#print('current try route cost:',route_cost)
	return route_cost 

def localSearch(route,dist_matrix=dm):
	#one step local search for neighborhood
	n_points = len(route)-1
	#	1. get possible neighborhood route, swap two nodes 
	#      (check from link_cost and tabu_list whether permitted, e.g.,
	#       whether two links to delete are in tabu_list)
	#   2. derive new links to add and links to delete
	#	3. add new links to both current_route and tabu_list
	
	# step 1, get pair nodes (i,j) to swap 
	current_cost = deriveCost(route,dist_matrix)
	new_route = None
	best_cost_reduction = 100000
	best_cost = 100000
	best_swap = None
	best_swap_ind = None
	#print("old route:",route)
	have_neighbour = False
	for i in range(1,n_points-1):
		for j in range(i+1,n_points):
			try_route = route[:]
			try_route[i:j+1] = route[j:i-1:-1] 
			new_cost = deriveCost(try_route,dist_matrix)
			cost_reduction = new_cost - current_cost
			#print("consider swap:",(route[i],route[j]))
			#print("potential new cost:",new_cost)
			if cost_reduction < best_cost_reduction:			
				links_to_delete_check = ((min(route[i-1],route[i]),max(route[i-1],route[i])),
				(min(route[j],route[j+1]),max(route[j],route[j+1]))) #sort the links in order of index
				if links_to_delete_check[0] in tabu_list and links_to_delete_check[1] in tabu_list:
					#print("rule out 1:",links_to_delete_check)
					continue
				bb = try_route[:]
				bb.reverse()
				if bb == route:
					continue	# rule out simple reversal of the tour
				best_swap = (route[i],route[j])
				best_swap_ind = (i,j)
				best_cost_reduction = cost_reduction
				new_route = try_route
				best_cost = new_cost
				have_neighbour = True
	#print("new route:",new_route, ",cost is:", best_cost, 
	#",swap element:", best_swap, ",swap index:",best_swap_ind)
	# step 2, derive links to add and delete
	p,q = best_swap_ind
	links_to_add = ((min(route[p-1],route[q]),max((route[p-1],route[q]))),
	(min(route[p],route[q+1]),max(route[p],route[q+1])))
	links_to_delete = ((min(route[p-1],route[p]),max(route[p-1],route[p])),
	(min(route[q],route[q+1]),max(route[q],route[q+1])))
	
	#print("links to add:", links_to_add)
	#print("links to delete:", links_to_delete)
	tabu_list.append(links_to_add[0])
	tabu_list.append(links_to_add[1])
	if len(tabu_list)>n_points//2+1:
		tabu_list.pop(0)		
		tabu_list.pop(0)
	#print("tabu list:",tabu_list)
	if not have_neighbour:
		return None
		
	return [new_route,best_cost] #return both new route and obj improvement

def tabuTSP():
	#main function of tabu search for MST problem
	dist_matrix = dm
	if not dist_matrix:
		dist_matrix = getInputData(inputdata)
	#current_route = initGreedySolution()
	current_route = [1,2,3,4,5,6,7,1]
	ct = 0 #count of consecutive non improvements
	solution = None
	optimal_cost = 100000
	k=1
	while True:
		#print("iteration ",k)
		k+=1
		res = localSearch(current_route)
		if res:
			best_cost = res[1]
			current_route = res[0]
			if optimal_cost <= best_cost: # no improvement on obj
				ct += 1
			else:
				optimal_cost = best_cost
				solution = current_route
				ct = 0 # reset ct to 0 if improved route is found
			if ct >= 3:
				#print("stop iteration after 3 consecutive non improvements!")
				#print("The solution is:",solution, ",cost is:",optimal_cost)
				return 
		else:
			#print("tabu stop, no available iterations!")
			#print("The solution is:", solution,",cost is:",optimal_cost)
			return 
	
def tabuTSP_coursera(inputdata):
	#main function of tabu search for MST problem
	n_points,dt_matrix = getInputData(inputdata)
	#current_route = initGreedySolution()
	#current_route = [1,2,3,4,5,6,7,1]
	current_route = [i for i in range(1,n_points+1)]
	current_route.append(1)
	ct = 0 #count of consecutive non improvements
	ct_lim = n_points//2
	solution = None
	optimal_cost = 10000000
	k=1
	while True:
		#print("iteration ",k)
		k+=1
		res = localSearch(current_route,dt_matrix)
		if res:
			best_cost = res[1]
			current_route = res[0]
			if optimal_cost <= best_cost: # no improvement on obj
				ct += 1
			else:
				optimal_cost = best_cost
				solution = current_route
				ct = 0 # reset ct to 0 if improved route is found
			if ct >= ct_lim:
				print("stop iteration after ",ct_lim," consecutive non improvements!")
				print("The solution is:",solution, ",cost is:",optimal_cost)
				return solution
		else:
			print("tabu stop, no available iterations!")
			print("The solution is:", solution,",cost is:",optimal_cost)
			return solution


		
#tabuTSP()
	
