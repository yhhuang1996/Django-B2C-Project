from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from apps.goods.models import *
from apps.order.models import *
from django_redis import get_redis_connection
from django.core.cache import cache


# Create your views here.
class IndexView(View):

    def get(self, request):
        """首页"""
        # 尝试从缓存中获取数据
        context = cache.get('index_page_data')
        if context is None:
            print('设置缓存')
            # 缓存中没有数据

            # 获取商品种类信息
            category = GoodsCategory.objects.all()

            # 获取首页轮播商品信息
            slide = IndexSlide.objects.all().order_by('index')

            # 获取首页促销活动信息
            promotion = IndexPromotion.objects.all().order_by('index')

            # 遍历每一个大分类，获取分类中放在首页的商品，并获取商品的展示方式
            for goods_cate in category:  # goods_cate是GoodsCategory的对象
                text_goods = IndexGoodsCategory.objects.filter(goods_category=goods_cate, show_method=0).order_by(
                    'index')
                image_goods = IndexGoodsCategory.objects.filter(goods_category=goods_cate, show_method=1).order_by(
                    'index')

                # 给category中的每个类都动态增加类属性，分别保存商品展示信息为文字还是图片
                # 通过类名添加的类属性，这个类的所有对象都能使用
                goods_cate.text_goods = text_goods  # goods_cate.text_goods是IndexGoodsCategory的对象集合
                goods_cate.image_goods = image_goods

            context = {'category': category,  # 新鲜水果、猪牛羊肉、家禽蛋类...集合
                       'slide': slide,
                       'promotion': promotion}

            # 设置缓存
            # key, value, timeout
            cache.set('index_page_data', context, 3600)

        # 获取购物车商品数量
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            con = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = con.hlen(cart_key)

        # 组织上下文
        context.update(cart_count=cart_count)
        return render(request, 'index.html', context)


# /goods/商品id
class DetailView(View):
    def get(self, request, goods_id):
        try:
            sku = GoodsSKU.objects.get(SKU_id=goods_id)
        except GoodsSKU.DoesNotExist:
            # 商品信息不存在
            return redirect(reverse('goods:index'))

        # 获取商品的分类信息
        category = GoodsCategory.objects.all()

        # 获取商品图片
        image = GoodsImage.objects.get(goodsSKU=sku)

        # 获取商品的评论信息
        comment = OrderGoods.objects.filter(SKU_id=sku).exclude(comment='')

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(category=sku.category).order_by('-create_time')[:2]

        # 获取购物车商品数量
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            con = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = con.hlen(cart_key)

            # 添加用户的历史浏览记录
            history_key = 'history_%d' % user.id
            # 移除goods_id
            con.lrem(history_key, 0, goods_id)
            # 插入最新浏览记录
            con.lpush(history_key, goods_id)
            # 只保存用户浏览的5条信息
            con.ltrim(history_key, 0, 4)

        # 组织模板上下文
        context = {'sku': sku, 'category': category, 'comment': comment, 'new_skus': new_skus, 'cart_count': cart_count,
                   'image': image}

        return render(request, 'detail.html', context)
