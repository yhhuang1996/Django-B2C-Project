from django.test import TestCase
from datetime import datetime
import os
from django.conf import settings

# Create your tests here.
di = {'code': '10000', 'msg': 'Success', 'buyer_logon_id': 'ieo***@sandbox.com', 'buyer_pay_amount': '0.00',
      'buyer_user_id': '2088102180459291', 'buyer_user_type': 'PRIVATE', 'invoice_amount': '0.00',
      'out_trade_no': '202003061549034', 'point_amount': '0.00', 'receipt_amount': '0.00',
      'send_pay_date': '2020-03-06 16:10:25', 'total_amount': '18.90', 'trade_no': '2020030622001459290500897364',
      'trade_status': 'TRADE_SUCCESS'}
