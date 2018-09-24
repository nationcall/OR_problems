//Hands on practices for reading cplex manual

#include <ilcplex/ilocplex.h>
#include <fstream>
#include <vector>
#include <math.h> 
ILOSTLBEGIN

/*
int main(int argc, char **argv){
	IloEnv env;
	IloModel mdl(env);//define model
	//IloNumVar myIntVar(env, -1, 10, ILOINT);
	//IloNumVarArray x(env, 3)
	IloNumVar x1(env,0,100,ILOINT),x2(env,0,100,ILOINT);
	
	int data[3][3] = {
		{2,1,100},
		{1,1,80},
		{1,0,40}
	};
	
	for(int i=0;i<3;i++){
		IloExpr expr(env);
		expr = data[i][0]*x1+data[i][1]*x2;
		mdl.add(expr<=data[i][2]);
	}
	IloObjective obj(env,3*x1+2*x2,IloObjective::Maximize);
	mdl.add(obj);
	
	IloCplex cplex(mdl);
	cplex.solve();
	if(cplex.getStatus()){
		IloNum val1 = cplex.getValue(x1);
		IloNum val2 = cplex.getValue(x2);
		IloNum objective = cplex.getObjValue();
		std::cout << "x1 is:" << val1 << std::endl;
		std::cout << "x2 is:" << val2 << std::endl;
		std::cout << "objective is:" << objective << std::endl;
	}
	env.end();

}
*/

// solve TSP problem 
using namespace std;
namespace tsp_example{
	typedef IloArray<IloNumVarArray> NumVarMatrix;
	vector< vector<double> > readInput(string filename){
		//read data from file for coordinates for locations, return data
		ifstream data_input;
		vector< vector<double> > data;
		data_input.open(filename);
		if(!data_input.is_open()){
			cout << "Unable to find the file!" << endl;
			return data;
		}
		string line;
		
		while(getline(data_input,line)){
			cout << line << endl;
			int n = line.length();
			char line_char[n+1];
			strcpy(line_char,line.c_str()); //convert string to char array
			char * token = strtok(line_char," "); //get first token (first number in the line)
			vector<double> rows;
			while (token != 0){
				//cout << "token:" << token << endl;
				rows.push_back(atof(token)); //convert char to int
				token = strtok(0," "); //move to next token
			}
			data.push_back(rows);
		}
		data_input.close();
		return data;
	}

	vector<vector<double> > calc_dist(vector<vector<double> > data){
		//calculate the distance between each location 
		int num_locations = data.size()-1;
		vector<vector<double> > distances;
		for(int i=0;i<num_locations;i++){
			vector<double> dis(num_locations,0); //initialize with 0s
			distances.push_back(dis);
		}
		for(int i=0;i<num_locations;i++){
			for(int j=0;j<num_locations;j++){
				distances[i][j]=sqrt(pow(data[i+1][0]-data[j+1][0],2)+
				pow(data[i+1][1]-data[j+1][1],2));
			}
		}
		return distances;
		
	}

	void formulateModel(vector< vector<double> >data, vector<vector<double> > distances){
		//formulate the optimization model
		//Objective:
		//
		//Decision variables:
		//  Integer decision variables x[i], x[i]=0,...,n-1
		//    	x[i] = k iff location i is visited at the k-th node in the tour 
		//  Binary decision variables R[i,j]
		//    	R[i,j] = 1 iff location i is visited just before location j
		//objective: 
		//		minimize sum of dist(x[i],x[i+1])
		//constraints: 
		//		x[i]!=x[j]                    (1)
		//		sum(i,R[i,j]) = 1             (2)
		//		sum(j,R[i,j]) = 1             (3)
		//		x[i]-x[j]+1 <= n*(1-R[i,j])   (4)  derived from: 1. R[i,j]=1 <=> x[i]-x[j]=-1, 2. R[i,j]=0 <=> x[i]-x[j]!=1
		int num_locations=data.size()-1;
		cout << "num_location = " << num_locations << endl;
		IloEnv env;
		IloModel mdl(env);
		
		IloNumVarArray x(env,num_locations,0,num_locations-1, ILOINT); //value range start from 1
		
		//constraint (1)
		for(int i=0;i<num_locations;i++){
			for(int j=i+1;j<num_locations;j++){
				mdl.add(x[i]!=x[j]);
			}
		}
		
		NumVarMatrix R; //assign variable matrix
		//initialize R
		for(int i=0;i<num_locations;i++){
			R[i] = IloNumVarArray(env,num_locations); //binary variable
			for(int j=0;j<num_locations;j++){
				R[i][j] = IloNumVar(env,0,1,ILOINT);
			}
		}
		//constraint (2)
		
		for(int i=0;i<num_locations;i++){
			IloExpr c1(env);
			for(int j=0;j<num_locations;j++){
				c1 += R[i][j];
			}
			mdl.add(c1 == 1);
		}
		//constraint (3)
		for(int j=0;j<num_locations;j++){
			IloExpr c1(env);
			for(int i=0;i<num_locations;i++){
				c1 += R[i][j];
			}
			mdl.add(c1 == 1);
		}
		//constraint (4)
		for(int i=0;i<num_locations;i++){
			for(int j=0;j<num_locations;j++){
				mdl.add(x[i]-x[j]+1 <= num_locations*(1-R[i][j])); 
			}
		}
		
		//objective
		IloExpr expr_obj(env);
		for(int i=0;i<num_locations;i++){
			for(int j=0;j<num_locations;j++){
				expr_obj += distances[i][j]*R[i][j];
			}	
		}
		IloObjective obj(env,expr_obj,IloObjective::Minimize);
		mdl.add(obj);
		IloCplex cplex(mdl);
		cplex.solve();
		if(cplex.getStatus()){
			//int* val1 = cplex.getValues(x);
			cout << "X value is:" << endl;
			for(int i=0;i<num_locations;i++){
				int val = cplex.getValue(x[i]);
				cout << val << ",";
			}
			//IloNum val2 = cplex.getValue(x2);
			IloNum objective = cplex.getObjValue();
			//std::cout << "x is:" << val1 << std::endl;
			std::cout << "objective is:" << objective << std::endl;
		}
		else{
			cout << "solution status failed!" << endl;
		}
		env.end();
	}

}

namespace optimus{
	void getModel(){
		IloEnv env;
		IloModel mdl(env);
		IloObjective obj;
		IloNumVarArray vars(env);
		IloRangeArray rngs(env);
		IloCplex cplex(env);
		try{
			cplex.importModel(mdl,"model_1809.lp",obj,vars,rngs);
			//cplex.extract(mdl);
			env.out() << "constraints size:" << rngs.getSize() << endl;
			rngs.remove(80,20);
			env.out() << "constraints size:" << rngs.getSize() << endl;
			IloNumArray vals(env);		
			cplex.solve();
			cplex.getValues(vals, vars);
			env.out() << "Solution status = " << cplex.getStatus() << endl;
			env.out() << "Solution value  = " << cplex.getObjValue() << endl;
			env.out() << "Solution vector = " << vals << endl;

		}
		catch(IloException &e){
			//env.error() << e << endl;
			cerr << "Concert exception caught:" << e << endl;
		}
		//env.out() << "Maximum bound violation = "
		//	<< cplex.getQuality(IloCplex::MaxPrimalInfeas) << endl;
		catch (...) {
			cerr << "Unknown exception caught" << endl;
		}
	}

}

int main(){
	//vector< vector<double> > data = tsp_example::readInput("/home/steve/Downloads/coursera_Dis_Opt/tsp/data/tsp_5_1");
	//vector< vector<double> > dists = tsp_example::calc_dist(data);

	//tsp_example::formulateModel(data,dists);
	optimus::getModel();
	return 0;
}
