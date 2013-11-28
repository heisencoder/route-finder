from django.template.loader import render_to_string
from django.http import HttpResponse


API_KEY1 = "AIzaSyDusgVbcYaUqaWD6-ORU2vHgE3mqwkKamA"
API_KEY2 = "AIzaSyAXQPThjgrcD_VOyfoD7_VLHJWGaQ1QBuI"


def staticFile(request, filename):
    rendered = render_to_string(filename)
    return HttpResponse(rendered)


def indexFile(request):
    filename = 'index.html'
    context = {"api_key" : API_KEY1}
    rendered = render_to_string(filename, context)
    return HttpResponse(rendered)
