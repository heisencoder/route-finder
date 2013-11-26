from django.shortcuts import render
from django.http import HttpResponse

def staticFile(request, filename):
    f = open('templates/%s' % (filename,), 'r')
    v = f.readlines()
    f.close()
    return HttpResponse(''.join(v))
