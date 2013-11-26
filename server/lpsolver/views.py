import json
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

import pymprog



def solveLP(n, data):    
    V = range(1, n+1)
    E = data.keys()

    p = pymprog.model("tsp")
    x = p.var(E, 'x', bool) # x created over index set E.
    # minize the total travel distance
    p.min(sum(data[t]*x[t] for t in E), 'totaldist')
    # subject to: leave each city exactly once
    p.st([sum(x[k,j] for j in V if (k,j) in E)==1 for k in V], 'leave')
    # subject to: enter each city exactly once
    p.st([sum(x[i,k] for i in V if (i,k) in E)==1 for k in V], 'enter')
    # We then need some flow constraints to eliminate subtours.
    # y: the number of cars carried: endowed with n at city 1.
    # exactly one car will be sold at each city.
    y=p.var(E, 'y') 
    p.st([(n-1)*x[t] >= y[t] for t in E], 'cap')
    p.st([sum(y[i,k] for i in V if (i,k) in E) + (n if k==1 else 0)
          ==sum(y[k,j] for j in V if (k,j) in E) + 1 for k in V], 'sale')

    p.solve(float) #solve as LP only.
    print "simplex done:", p.status()
    p.solve(int) #solve the IP problem

    # The optimal solution is 6859
    print(p.vobj())
    tour = [t for t in E if x[t].primal>.5]
    cat, car = 1, n
    print("This is the optimal tour with [cars carried]:")
    ztour = []
    for k in V: 
        #print cat,
        for i,j in tour: 
            if i==cat: 
                #print "[%g]"%y[i,j].primal,
                ztour.append(cat)
                cat=j
                break

    # Tour is list of edge tuples
    # ztour, list of destinations
    return ztour


# Is this correctly solving the problem?

# This decorator marks a view as being exempt from the protection ensured by the middleware.
# Needed or we get a 403 on all POST requests
@csrf_exempt
def solverRequest(request):
    print 'SOLVER REQUEST'
    if request.method == 'POST':
        #json_data = json.loads(request.raw_post_data)
        print 'Raw Data: "%s"' % request.body
    # Solves TSP given graph weights as list of list
    # First index is source
    data = json.loads(request.body)
    #print "start:", data["start"]
    #print "n:", data["n"]
    #print "travelMatrix[%s]" % (len(data["travelMatrix"]),)

    n = data["n"]
    start = data["start"]
    end = data["end"]
    travelMatrix = data["travelMatrix"]

    graphDict = {}
    for i in range(0, n):
        for j in range(0, n):
            # {(16,13):406, (16,14):449, (16,15):636}"
            graphDict[(i+1, j+1)] = travelMatrix[i][j]

    route = solveLP(n, graphDict)
    # print route
    resp = json.dumps(route)

    # #return HttpResponse('OK)
    return HttpResponse(resp)
