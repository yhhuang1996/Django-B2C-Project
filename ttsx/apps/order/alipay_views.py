import logging
import os
import traceback

from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest
from alipay.aop.api.response.AlipayTradePayResponse import AlipayTradePayResponse
from django.http import JsonResponse
from django.views.generic import View
from django.conf import settings
from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.domain.AlipayTradeCreateModel import AlipayTradeCreateModel
from alipay.aop.api.request.AlipayTradeCreateRequest import AlipayTradeCreateRequest


# 实例化客户端
def ali_pay():
    # 日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        filemode='a', )
    logger = logging.getLogger('')

    alipay_client_config = AlipayClientConfig(sandbox_debug=True)
    alipay_client_config.app_id = '2016101900723921'
    alipay_client_config.app_private_key = ''
    alipay_client_config.alipay_public_key = ''
    alipay_client_config.sign_type = 'RSA2'
    alipay_client_config.charset = 'utf-8'
    client = DefaultAlipayClient(alipay_client_config=alipay_client_config, logger=logger)

    return client


# 构造请求参数对象
def ali_pay_view(client, order_id, order, user):
    model = AlipayTradePagePayModel()
    model.out_trade_no = order_id
    model.total_amount = str(order.total_pay)
    model.subject = "天天生鲜%s" % order_id
    model.buyer_id = str(user.id)
    request = AlipayTradePagePayRequest(biz_model=model)

    # # 返回应答
    # response_content = None
    try:
        response = client.page_execute(request, http_method="GET")
        print(response)
    #     return JsonResponse({'res': 3, 'response_url': response_content})
    except Exception as e:
        # print(traceback.format_exc())
        print('失败')
    # if not response_content:
    #     print("failed execute")
    #     return JsonResponse({'res': 4, 'error_msg': '支付错误'})
    # else:
    #     response = AlipayTradePayResponse()
    #     # 解析响应结果
    #     response.parse_response_content(response_content)
    #     print(response.body)
    #     if response.is_success():
    #         # 如果业务成功，则通过response属性获取需要的值
    #         print("get response trade_no:" + response.trade_no)
    #     else:
    #         # 如果业务失败，则从错误码中可以得知错误情况，具体错误码信息可以查看接口文档
    #         print(response.code + "," + response.msg + "," + response.sub_code + "," + response.sub_msg)
    #
    # return model, request
