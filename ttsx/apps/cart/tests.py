from django.test import TestCase

# Create your tests here.
a = [b'6', b'3']
s = 0
for i in a:
    s += int(i.decode())

print(s)