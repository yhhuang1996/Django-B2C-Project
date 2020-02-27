from django.shortcuts import render
from django.views.generic import View
from apps.goods.models import *
from django_redis import get_redis_connection


# Create your views here.
class IndexView(View):

    def get(self, request):
        """首页"""
        # 获取商品种类信息
        category = GoodsCategory.objects.all()

        # 获取首页轮播商品信息
        slide = IndexSlide.objects.all().order_by('index')

        # 获取首页促销活动信息
        promotion = IndexPromotion.objects.all().order_by('index')

        # 遍历每一个大分类，获取分类中放在首页的商品，并获取商品的展示方式
        for goods_cate in category:  # goods_cate是GoodsCategory的对象
            text_goods = IndexGoodsCategory.objects.filter(goods_category=goods_cate, show_method=0).order_by('index')
            image_goods = IndexGoodsCategory.objects.filter(goods_category=goods_cate, show_method=1).order_by('index')

            # 给category中的每个类都动态增加类属性，分别保存商品展示信息为文字还是图片
            # 通过类名添加的类属性，这个类的所有对象都能使用
            goods_cate.text_goods = text_goods  # goods_cate.text_goods是IndexGoodsCategory的对象集合
            goods_cate.image_goods = image_goods

        # 获取购物车商品数量
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            con = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = con.hlen(cart_key)

        # 组织上下文
        context = {'category': category,  # 新鲜水果、猪牛羊肉、家禽蛋类...集合
                   'slide': slide,
                   'promotion': promotion,
                   'cart_count': cart_count,
                   }
        return render(request, 'index.html', context)