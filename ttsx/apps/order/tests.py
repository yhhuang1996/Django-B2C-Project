from django.test import TestCase
from datetime import datetime

# Create your tests here.
s = '100001,100031'
s_list = s.split(',')
print(*s_list)
