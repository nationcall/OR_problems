from ortools.constraint_solver import pywrapcp
from ortools.linear_solver import pywraplp


'''
1. input data: 
    a. list of size of finals, 
    b. list of demand for each size of finals,
    c. size of raw

2. solve the master sub problem:
    a. init the solution 
    b. get current columns 
    c. solve to get the shadow price
3. solve the dual problem (knapsack problem):
    a. use the shadow price in step 2 to formulate the dual problem
    b. solve the problem

'''

def dataInput():

    return


def formMasterSubProblem(raw_length, size_demand, size_length):

    # raw_length: scalar, length of raw
    # size_demand: list, demand of each size of finals
    # size_length: list, total number of distinct finals
    solver = pywraplp.Solver('masterSub', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    # assign a decision variable for each pattern, initially pattern number is same as number of finals
    n_types = len(size_demand)
    assign_vars = [solver.NumVar(0, raw_length, 'x_'+str(i)) for i in range(n_types)]
    # number can cut for each pattern
    num_cut = [(raw_length//i) for i in size_length]
    for i in range(n_types):
        solver.Add(num_cut[i]*assign_vars[i] >= size_demand[i], 'demand_constraint'+str(i))

    z = solver.Sum(assign_vars)
    objective = solver.Minimize(z)
    solver.Solve()
    print('objective:', solver.Objective().Value())
    print('x:', end=' ')
    for i in range(n_types):
        print(assign_vars[i].SolutionValue(), end=' ')
    print('dual value:', solver.Constraint('demand_constraint_1').dual_value())

    return

raw_length = 17
size_demand = [25, 20, 15]
size_length = [3, 5, 9]

formMasterSubProblem(raw_length, size_demand, size_length)