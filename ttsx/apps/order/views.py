from django.shortcuts import render, redirect
from django.views.generic import View
from django.urls import reverse
from django.http import JsonResponse
from apps.goods.models import GoodsSKU
from apps.user.models import Address
from apps.order.models import *
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime
from django.db import transaction


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


