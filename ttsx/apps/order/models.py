from django.db import models
from db.base_model import BaseModel
from apps.user.models import *
from apps.goods.models import *
# Create your models here.


class OrderInfo(BaseModel):
    """订单信息模型类"""
    pay_method_dict = {
        '1': '货到付款',
        '2': '微信支付',
        '3': '支付宝',
        '4': '银联支付',
    }

    order_status_dict = {
        '1': '待支付',
        '2': '待发货',
        '3': '待收货',
        '4': '待评价',
        '5': '已完成',
    }

    pay_method_choice = (
        (1, '货到付款'),
        (2, '微信支付'),
        (3, '支付宝'),
        (4, '银联支付'),
    )
    order_status_choice = (
        (1, '待支付'),
        (2, '待发货'),
        (3, '待收货'),
        (4, '待评价'),
        (5, '已完成'),
    )
    order_id = models.CharField(max_length=128, primary_key=True, verbose_name='订单编号')
    user_id = models.ForeignKey(User, verbose_name='用户ID', on_delete=models.CASCADE)
    addr_id = models.ForeignKey(Address, verbose_name='地址ID', on_delete=models.CASCADE)
    pay_method = models.SmallIntegerField(choices=pay_method_choice, verbose_name='支付方式')
    total_count = models.IntegerField(verbose_name='总数量')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='总商品金额')
    express_fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='快递费')
    total_pay = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='总支付金额')
    order_status = models.IntegerField(choices=order_status_choice, default='1', verbose_name='订单状态')
    trade_num = models.CharField(max_length=128, default='', verbose_name='支付编号')

    class Meta:
        db_table = 'order_info'
        verbose_name = '订单信息'
        verbose_name_plural = verbose_name


class OrderGoods(BaseModel):
    """订单商品模型类"""
    order_id = models.ForeignKey(OrderInfo, verbose_name='订单ID', on_delete=models.CASCADE)
    SKU_id = models.ForeignKey(GoodsSKU, verbose_name='商品ID', on_delete=models.CASCADE)
    count = models.IntegerField(default=1, verbose_name='数量')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格')
    comment = models.CharField(max_length=512, default='', verbose_name='评价')

    class Meta:
        db_table = 'order_goods'
        verbose_name = '订单商品'
        verbose_name_plural = verbose_name
