from django.template.loader import render_to_string
from django.http import HttpResponse


API_KEY = "AIzaSyDusgVbcYaUqaWD6-ORU2vHgE3mqwkKamA"

def staticFile(request, filename):
    rendered = render_to_string(filename, {"api_key" : API_KEY})
    return HttpResponse(rendered)
