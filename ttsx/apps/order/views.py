import os
from django.shortcuts import render, redirect
from django.views.generic import View
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from apps.goods.models import GoodsSKU
from apps.user.models import Address
from apps.order.models import *
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime
from django.db import transaction
from django.conf import settings
from alipay import AliPay, ISVAliPay
import time
import ssl


# Create your views here.
class PlaceOrderView(LoginRequiredMixin, View):
    def post(self, request):
        # 接收数据
        skus = request.POST.getlist('sku_id')

        # 校验数据
        if not skus:
            return redirect(reverse('cart:cart'))

        # 业务处理
        con = get_redis_connection('default')
        user = request.user
        cart_key = 'cart_%d' % user.id

        sku_list = []
        total_price, total_count = 0, 0
        for sku in skus:
            sku = GoodsSKU.objects.get(SKU_id=sku)
            count = int(con.hget(cart_key, sku.SKU_id))
            amount = sku.price * count
            sku.count = count
            sku.amount = amount
            total_count += count
            total_price += amount
            sku_list.append(sku)

        # 运费
        if total_price >= 59:
            transit_price = 0
        else:
            transit_price = 15

        # 实付款
        total_pay = total_price + transit_price

        # 获取用户地址
        address = Address.objects.filter(user=user)

        sku_ids = ','.join(skus)
        context = {'sku_list': sku_list,
                   'total_count': total_count,
                   'total_price': total_price,
                   'transit_price': transit_price,
                   'total_pay': total_pay,
                   'address': address,
                   'sku_ids': sku_ids}
        # 返回应答
        return render(request, 'place_order.html', context)


# 悲观锁
class OrderCommit1View(View):
    """订单创建"""
    @transaction.atomic
    def post(self, request):
        # TODO: 验证用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': -1, 'error_msg': '用户未登录'})

        # TODO: 接收数据
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        # TODO: 数据验证
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 0, 'error_msg': '数据不完整'})
        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 1, 'error_msg': '地址不存在'})
        # 校验支付方式
        if pay_method not in OrderInfo.pay_method_dict.keys():
            return JsonResponse({'res': 2, 'error_msg': '支付方式错误'})
        # 校验商品id及库存，由于开启事务，可在后方执行，遍历一次sku_ids，以提高效率

        # 添加保存点
        save_id = transaction.savepoint()

        # TODO: 创建订单核心任务
        # TODO: 向订单信息表中加入一条数据
        try:
            # 组织参数
            # 订单id: 时间+用户id
            order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
            # 暂时定义商品总数目、总金额及运费
            total_count, total_price, express_fee, total_pay = 0, 0, 0, 0

            order = OrderInfo.objects.create(order_id=order_id,
                                             user_id=user,
                                             addr_id=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             express_fee=express_fee,
                                             total_pay=total_pay,
                                             )

            # 从redis中拿出商品数量
            con = get_redis_connection('default')
            cart_key = "cart_%d" % user.id

            # TODO: 向订单商品表中加入商品数据
            sku_list = sku_ids.split(',')
            for sku_id in sku_list:
                # 校验商品id
                try:
                    # 悲观锁
                    # select * from goods_SKU where id=SKU_id for update;
                    sku = GoodsSKU.objects.select_for_update().get(SKU_id=sku_id)
                    # sku = GoodsSKU.objects.get(SKU_id=sku_id)
                except GoodsSKU.DoesNotExist:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 3, 'error_msg': '商品不存在'})
                # 判断商品库存
                count = int(con.hget(cart_key, sku_id))
                if count > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'error_msg': '商品库存不足'})

                OrderGoods.objects.create(order_id=order,
                                          SKU_id=sku,
                                          count=count,
                                          price=sku.price
                                          )
                # 更新商品库存和销量
                sku.stock -= count
                sku.sale_count += count
                sku.save()

                # 计算订单商品总数目和总价格
                amount = sku.price * count
                total_count += count
                total_price += amount

            # 计算运费
            if total_price >= 59:
                express_fee = 0
            else:
                express_fee = 15
            total_pay = total_price + express_fee
            # 更新订单信息表中总数目、总金额及运费
            order.total_count = total_count
            order.total_price = total_price
            order.express_fee = express_fee
            order.total_pay = total_pay
            order.save()
        except Exception as ret:
            print(ret)
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 5, 'error_msg': '下单失败'})

        # 提交事务
        transaction.savepoint_commit(save_id)
        # 清除用户购物车中对应记录
        con.hdel(cart_key, *sku_list)

        return JsonResponse({'res': 10, 'msg': '创建成功'})


# 乐观锁
class OrderCommitView(View):
    """订单创建"""
    @transaction.atomic
    def post(self, request):
        # TODO: 验证用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': -1, 'error_msg': '用户未登录'})

        # TODO: 接收数据
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        # TODO: 数据验证
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 0, 'error_msg': '数据不完整'})
        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 1, 'error_msg': '地址不存在'})
        # 校验支付方式
        if pay_method not in OrderInfo.pay_method_dict.keys():
            return JsonResponse({'res': 2, 'error_msg': '支付方式错误'})
        # 校验商品id及库存，由于开启事务，可在后方执行，遍历一次sku_ids，以提高效率

        # 添加保存点
        save_id = transaction.savepoint()

        # TODO: 创建订单核心任务
        # TODO: 向订单信息表中加入一条数据
        try:
            # 组织参数
            # 订单id: 时间+用户id
            order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
            # 暂时定义商品总数目、总金额及运费
            total_count, total_price, express_fee, total_pay = 0, 0, 0, 0

            order = OrderInfo.objects.create(order_id=order_id,
                                             user_id=user,
                                             addr_id=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             express_fee=express_fee,
                                             total_pay=total_pay,
                                             )

            # 从redis中拿出商品数量
            con = get_redis_connection('default')
            cart_key = "cart_%d" % user.id

            # TODO: 向订单商品表中加入商品数据
            sku_list = sku_ids.split(',')
            for sku_id in sku_list:
                for i in range(3):
                    # 校验商品id
                    try:
                        sku = GoodsSKU.objects.get(SKU_id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 3, 'error_msg': '商品不存在'})
                    # 判断商品库存
                    count = int(con.hget(cart_key, sku_id))
                    if count > sku.stock:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 4, 'error_msg': '商品库存不足'})

                    # 更新商品的库存和销量
                    origin_stock = sku.stock
                    new_stock = origin_stock - count
                    new_sale_count = origin_stock + count

                    # TODO: 乐观锁，返回查询结果的行数  djando2.X后 mysql事务隔离级别默认设为读已提交
                    # 把更新提到添加记录的前面，防止数据重复提交进数据库
                    # update goods_SKU set stock=new_stock, sale_count=new_sale_count where id=SKU_id and stock=origin_stock
                    res = GoodsSKU.objects.filter(SKU_id=sku_id, stock=origin_stock).\
                        update(stock=new_stock, sale_count=new_sale_count)
                    if res == 0:
                        # 尝试的第三次
                        if i == 2:
                            # 更新失败
                            transaction.rollback(save_id)
                            return JsonResponse({'res': 6, 'error_msg': '库存不足，下单失败'})
                        continue

                    OrderGoods.objects.create(order_id=order,
                                              SKU_id=sku,
                                              count=count,
                                              price=sku.price
                                              )

                    # 计算订单商品总数目和总价格
                    amount = sku.price * count
                    total_count += count
                    total_price += amount

                    # 跳出循环
                    break

            # 计算运费
            if total_price >= 59:
                express_fee = 0
            else:
                express_fee = 15
            total_pay = total_price + express_fee
            # 更新订单信息表中总数目、总金额及运费
            order.total_count = total_count
            order.total_price = total_price
            order.express_fee = express_fee
            order.total_pay = total_pay
            order.save()
        except Exception as ret:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 5, 'error_msg': '下单失败'})

        # 提交事务
        transaction.savepoint_commit(save_id)
        # 清除用户购物车中对应记录
        con.hdel(cart_key, *sku_list)

        return JsonResponse({'res': 10, 'msg': '创建成功'})


class OrderPayView(View):
    """订单支付"""
    def post(self, request):
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': -1, 'error_msg': '用户未登录'})
        # 接收参数
        order_id = request.POST.get('order_id')
        # 校验参数
        if not order_id:
            return JsonResponse({'res': 0, 'error_msg': '订单不存在'})
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user_id=user.id,
                                          pay_method=3,
                                          order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 1, 'error_msg': '订单错误'})
        # TODO: 业务处理：调用支付宝的支付接口

        # # 实例化客户端对象
        # client = ali_pay()
        # # 生成支付宝自带页面API
        # request = ali_pay_view(client, order_id, order, user)
        # print(client)
        # return JsonResponse({'res': 2, 'client': '客户端对象'})
        app_private_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/')+"app_private_key.pem").read()
        alipay_public_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/')+"alipay_public_key.pem").read()
        alipay = AliPay(
            appid="2016101900723921",
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )

        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_pay),
            subject="天天生鲜%s" % order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        # 返回应答
        pay_url = "https://openapi.alipaydev.com/gateway.do?" + order_string
        return JsonResponse({'res': 3, 'pay_url': pay_url})


class OrderCheckView(View):
    """查看订单支付结果"""
    def post(self, request):
        ssl._create_default_https_context = ssl._create_unverified_context
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': -1, 'error_msg': '用户未登录'})
        # 接收参数
        order_id = request.POST.get('order_id')
        # 校验参数
        if not order_id:
            return JsonResponse({'res': 0, 'error_msg': '订单不存在'})
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user_id=user.id,
                                          pay_method=3,
                                          order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 1, 'error_msg': '订单错误'})

        app_private_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/') + "app_private_key.pem").read()
        alipay_public_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/') + "alipay_public_key.pem").read()
        alipay = AliPay(
            appid="2016101900723921",
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )
        # 调用支付查询接口
        # paid = False
        # for i in range(10):
        #     # check every 3s, and 10 times in all
        #     print("now sleep 3s")
        #     time.sleep(3)
        #     result = alipay.api_alipay_trade_query(out_trade_no=order_id)
        #     print('result------------', result)
        #     if result.get("trade_status", "") == "TRADE_SUCCESS":
        #         paid = True
        #         break
        #     print("not paid...")
        #
        # return JsonResponse({'res': 4, 'msg': '支付成功'})
        #
        while True:
            response = alipay.api_alipay_trade_query(out_trade_no=order_id)
            code = response.get('code')
            trade_status = response.get('trade_status')
            if code == '10000' and trade_status == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')
                # 更新订单状态
                order.trade_num = trade_no
                order.order_status = 4  # 待评价
                order.save()
                return JsonResponse({'res': 4, 'msg': '支付成功'})

            elif code == '40004' or (code == '10000' and trade_status == 'WAIT_BUYER_PAY'):
                # 待买家支付
                time.sleep(1)
                continue
            else:
                return JsonResponse({'res': 5, 'error_msg': '支付出错'})


class CommentView(LoginRequiredMixin, View):
    """评论"""
    def get(self, request, order_id):
        user = request.user

        if not order_id:
            return redirect(reversed('user:order'))
        try:
            order = OrderInfo.objects.get(order_id=order_id, user_id=user)
        except OrderInfo.DoesNotExist:
            return redirect(reversed('user:order'))

        # 根据订单的状态获取订单的状态标题
        order.status_name = OrderInfo.order_status_dict[str(order.order_status)]
        # 获取订单商品信息
        order_goods = OrderGoods.objects.filter(order_id=order_id)
        for goods in order_goods:
            amount = goods.price * goods.count
            goods.amount = amount
        order.order_goods = order_goods

        return render(request, 'order_comment.html', {'order': order})

    def post(self, request, order_id):
        user = request.user

        if not order_id:
            return redirect(reversed('user:order'))
        try:
            order = OrderInfo.objects.get(order_id=order_id, user_id=user)
        except OrderInfo.DoesNotExist:
            return redirect(reversed('user:order'))

        # 获取评论条数
        total_count = request.POST.get('total_count')
        total_count = int(total_count)

        for i in range(1, total_count+1):
            # 获取评论的商品的id
            sku_id = request.POST.get('sku_%d' % i)
            # 获取对应的评论
            content = request.POST.get('content_%d' % i, '')
            print(sku_id+":"+content)

            try:
                print(order_id, sku_id)
                order_goods = OrderGoods.objects.get(order_id=order_id, SKU_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5
        order.save()

        return redirect(reverse('user:order', kwargs={'page': 1}))