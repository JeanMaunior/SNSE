from os import popen
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'SNsearcher.settings'

print('Server opened.')
result = popen('python manage.py runserver 127.0.0.1:8000')
res = result.read()
for line in res.splitlines():
    print(line)