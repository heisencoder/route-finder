import json
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

import pymprog



def solveLP(n, data, returnBack):    
    V = range(1, n+1)
    E = data.keys()

    p = pymprog.model("tsp")
    x = p.var(E, 'x', bool) # x created over index set E.
    # minize the total travel distance
    p.min(sum(data[t]*x[t] for t in E), 'totaldist')
    # subject to: leave each city exactly once
    p.st([sum(x[k,j] for j in V if (k,j) in E)==1 for k in V], 'leave')
    # subject to: enter each city exactly once
    # TODO: unclosed route? if(returnBack) V[1:]
    p.st([sum(x[i,k] for i in V if (i,k) in E)==1 for k in V], 'enter')
    # We then need some flow constraints to eliminate subtours.
    # y: the number of cars carried: endowed with n at city 1.
    # exactly one car will be sold at each city.
    y=p.var(E, 'y') 
    p.st([(n-1)*x[t] >= y[t] for t in E], 'cap')
    p.st([sum(y[i,k] for i in V if (i,k) in E) + (n if k==1 else 0)
          ==sum(y[k,j] for j in V if (k,j) in E) + 1 for k in V], 'sale')

    p.solve(float) #solve as LP only.
    #print "simplex done:", p.status()
    p.solve(int) #solve the IP problem

    # The optimal solution is 6859
    print(p.vobj())
    tour = [t for t in E if x[t].primal>.5]  # list of tuples (i,j)
    itinerary = []  # ordered list of destinations
    cat, car = 1, n
    #print("This is the optimal tour with [cars carried]:")
    for k in V: 
        #print cat,
        for i,j in tour: 
            if i==cat: 
                #print "[%g]"%y[i,j].primal,
                itinerary.append(cat)
                cat=j
                break
    return itinerary


# This decorator marks a view as being exempt from the protection ensured by the middleware. Needed or we get a 403 on all POST requests
@csrf_exempt
def solverRequest(request):
    print 'SOLVER REQUEST'
    if request.method != 'POST':
        print "POST expected!"
    #print 'Raw Data: "%s"' % request.body

    # Solves TSP given graph weights as list of list [source][dest]
    data = json.loads(request.body)
    n = data["n"]
    start = data["start"]
    if "end" in data:
        returnBack = True
    else:
        returnBack = False
    travelMatrix = data["travelMatrix"]

    # For now, build graph as dictionary (as in sample code)
    # {(16,13):406, (16,14):449, (16,15):636}"
    graphDict = {}
    for i in range(0, n):
        for j in range(0, n):
            graphDict[(i+1, j+1)] = travelMatrix[i][j]

    route = solveLP(n, graphDict, returnBack)
    print route
    resp = json.dumps(route)

    return HttpResponse(resp)
