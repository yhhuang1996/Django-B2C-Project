import os
from django.views.generic import View
from django.conf import settings
from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.domain.AlipayTradeCreateModel import AlipayTradeCreateModel
from alipay.aop.api.request.AlipayTradeCreateRequest import AlipayTradeCreateRequest


# 实例化客户端
def ali_pay():
    alipay_client_config = AlipayClientConfig()
    alipay_client_config.server_url = 'https://openapi.alipaydev.com/gateway.do'
    alipay_client_config.app_id = '2016101900723921'
    alipay_client_config.app_private_key = open(
        os.path.join(settings.BASE_DIR, 'apps/order/') + "app_private_key.txt").read()
    alipay_client_config.alipay_public_key = open(
        os.path.join(settings.BASE_DIR, 'apps/order/') + "alipay_public_key.txt").read()
    return alipay_client_config


# 构造请求参数对象
def ali_pay_view(order_id, order, user):
    model = AlipayTradeCreateModel()
    model.out_trade_no = order_id
    model.total_amount = str(order.total_pay)
    model.subject = "天天生鲜%s" % order_id
    model.buyer_id = str(user.id)
    request = AlipayTradeCreateRequest(biz_model=model)
    return model, request
