import json
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

import pymprog

# Is this correctly solving the problem?

# This decorator marks a view as being exempt from the protection ensured by the middleware.
# Needed or we get a 403 on all POST requests
@csrf_exempt
def solverRequest(request):
    print 'SOLVER REQUEST'
    if request.method == 'POST':
        #json_data = json.loads(request.raw_post_data)
        print 'Raw Data: "%s"' % request.body
    # Solves TSP given raw data like:
    #    "{(1,2):509, (1,3):501, (1,4):312, ..."

    # Should do some sanity checking
    data = eval(request.body)
    n = 16 # can i infer?
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
    for k in V: 
        print cat,
        for i,j in tour: 
            if i==cat: 
                print "[%g]"%y[i,j].primal,
                cat=j
                break
    print cat


    # can also produce json in response
    #return HttpResponse('OK)
    return HttpResponse(cat)
