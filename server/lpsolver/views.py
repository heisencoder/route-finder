import datetime
import json
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

import pymprog

def solveLP(n, data, returnBack):
    startTime = datetime.datetime.now()
    V = range(1, n+1)
    E = data.keys()

    p = pymprog.model("tsp")
    x = p.var(E, 'x', bool) # x created over index set E.
    v = p.var(V, 'v', bool) # v[k] == 1 implies last node, sum(y[k, i] = 0)
    # minize the total travel distance
    p.min(sum([data[t]*x[t] for t in E] + [v[i] for i in V]), 'totaldist')
    # subject to: leave each city exactly once
    p.st([sum([x[k,j] for j in V if (k,j) in E] + [v[k]])==1 for k in V], 'leave')
    # subject to: enter each city exactly once
    if returnBack:
        p.st([sum(x[i,k] for i in V if (i,k) in E)==1 for k in V], 'enter')
    else:
        p.st([sum(x[i,k] for i in V if (i,k) in E)==1 for k in V[1:]], 'enter')
    # We then need some flow constraints to eliminate subtours.
    # y: the number of cars carried: endowed with n at city 1.
    # exactly one car will be sold at each city.
    y=p.var(E, 'y')
    p.st([(n-1)*x[t] >= y[t] for t in E], 'cap')
    p.st([sum(y[i,k] for i in V if (i,k) in E) + (n if k==1 else 0)
          ==sum(y[k,j] for j in V if (k,j) in E) + 1 for k in V], 'sale')
    if not returnBack:
        # Without this, simply all v[i] == 0
        # v[i] set only when sum(y[i,j] for j in V)
        p.st([sum([y[i,j] for j in V] + [v[i]]) >= 1 for k in V], 'open')

    p.solve(float) #solve as LP only.
    #print "simplex done:", p.status()
    p.solve(int) #solve the IP problem

    print(p.vobj())
    # print "Edges:"
    # for t in E:
    #     print "x%s = %d" % (t, x[t].primal)
    # print "T's:"
    # for t in E:
    #     print "y%s = %d" % (t, y[t].primal)
    # print "vs:"
    # for d in V:
    #     print "v[%d] = %d" % (d, v[d].primal)

    tour = [t for t in E if x[t].primal>.5]  # list of tuples (i,j)
    tour.sort(key=lambda t: n-y[t].primal-1) # organize links by car number in reverse
    # automatically includes trailing [1] if returnBack
    itinerary = [1] + [v[1] for v in tour]
    endTime = datetime.datetime.now()
    print "Time required to solve LP: %f" % (endTime - startTime).total_seconds()

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
