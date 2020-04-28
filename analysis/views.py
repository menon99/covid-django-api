from django.http import JsonResponse
import os
# Create your views here.


def hello(request):

    path = os.getcwd().split('/')
    if path[-1] != 'csv':
        os.chdir('analysis/csv')
    f = open('hello.txt')
    contents = f.read()
    i = int(contents.strip())
    print('cwd is ', os.getcwd())
    obj = {
        'name': 'akash',
        'age': i
    }
    return JsonResponse(obj)
