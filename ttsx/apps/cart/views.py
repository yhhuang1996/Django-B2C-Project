from django.shortcuts import render
from django.views.generic import View
from django.http.response import JsonResponse
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.


class CartAddView(View):
    """购物车记录添加"""
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': -1, 'error_msg': '用户未登录'})
        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 数据校验
        if not all([sku_id, count]):
            return JsonResponse({'res': 0, 'error_msg': '数据不完整'})
        # 校验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            # 数目出错
            JsonResponse({'res': 1, 'error_msg': '商品数目出错'})
        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(SKU_id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'error_msg': '商品不存在'})

        # 业务处理：添加到购物车
        con = get_redis_connection('default')
        # 先尝试获取sku_id的值

        cart_key = 'cart_%d' % user.id
        # 若sku_id在哈希表中不存在，hget返回None
        cart_count = con.hget(cart_key, sku_id)
        if cart_count:
            count += int(cart_count)
        # 校验商品库存
        stock = sku.stock
        if count > stock:
            return JsonResponse({'res': 3, 'error_msg': '商品库存不足'})
        # 设置hash中sku_id对应的值
        con.hset(cart_key, sku_id, count)

        # 计算购物车商品条目数
        cart_num = con.hlen(cart_key)

        # 返回应答
        return JsonResponse({'res': 4, 'msg': '添加成功', 'cart_num': cart_num})


class CartView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        con = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        sku_list = []
        total_goods, total_price = 0, 0
        # {'商品id': 商品数量}
        goods_dict = con.hgetall(cart_key)
        for sku, count in goods_dict.items():
            sku = sku.decode()
            count = int(count.decode())
            sku = GoodsSKU.objects.get(SKU_id=sku)
            amount = sku.price * count  # 商品小计

            sku.amount = amount  # 动态给sku增加amount属性
            sku.count = count  # 动态给sku增加数量属性

            total_goods += count  # 商品总件数
            total_price += amount  # 商品合计
            sku_list.append(sku)

        # 接收数据

        # 校验数据
        # 业务处理
        # 返回应答
        context = {'total_goods': total_goods, 'total_price': total_price, 'sku_list': sku_list}
        return render(request, 'cart.html', context)


# 更新购物车记录
# 采用ajax post请求
# 前端需要传递的参数：商品id 数目
class CartUpdateView(View):
    def post(self, request):

        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': -1, 'error_msg': '用户未登录'})
        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 数据校验
        if not all([sku_id, count]):
            return JsonResponse({'res': 0, 'error_msg': '数据不完整'})
        # 校验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            # 数目出错
            JsonResponse({'res': 1, 'error_msg': '商品数目出错'})
        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(SKU_id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'error_msg': '商品不存在'})

        # 业务处理
        con = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 校验商品库存
        stock = sku.stock
        if count > stock:
            return JsonResponse({'res': 3, 'error_msg': '商品库存不足', 'stock': stock})
        con.hset(cart_key, sku_id, count)

        # 计算购物车总件数
        per_count = con.hvals(cart_key)
        total_count = 0
        for i in per_count:
            total_count += int(i.decode())

        # 返回应答
        return JsonResponse({'res': 5, 'msg': '更新成功', 'total_count': total_count})


class CartDeleteView(View):
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': -1, 'error_msg': '用户未登录'})
        #  接收参数
        sku_id = request.POST.get('sku_id')
        # 数据校验
        if not all([sku_id]):
            return JsonResponse({'res': 0, 'error_msg': '数据不完整'})
        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(SKU_id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 1, 'error_msg': '商品不存在'})

        # 业务处理
        con = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        con.hdel(cart_key, sku_id)

        # 计算购物车总件数
        per_count = con.hvals(cart_key)
        total_count = 0
        for i in per_count:
            total_count += int(i.decode())

        return JsonResponse({'res': 2, 'msg': '删除成功', 'total_count': total_count})