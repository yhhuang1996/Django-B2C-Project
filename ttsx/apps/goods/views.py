from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from apps.goods.models import *
from apps.order.models import *
from django_redis import get_redis_connection
from django.core.cache import cache
from django.core.paginator import Paginator


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

        # 获取同一个SPU的其它规格商品
        same_spu_skus = GoodsSKU.objects.filter(goodsSPU=sku.goodsSPU).exclude(SKU_id=goods_id)

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
                   'image': image, 'same_spu_skus': same_spu_skus}

        return render(request, 'detail.html', context)


# goods_list/分类/page?sort
class ListView(View):
    """商品分类列表"""

    def get(self, request, category_id, page):
        try:
            category_id = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            # 商品种类信息不存在
            return redirect(reverse('goods:index'))

        # 获取商品的分类信息
        category = GoodsCategory.objects.all()

        # 获取新品
        new_goods = GoodsSKU.objects.filter(category=category_id).order_by('-update_time')[:2]

        # 排序方式
        sort = request.GET.get('sort')
        if sort == 'price':
            # 价格排序
            goods_list = GoodsSKU.objects.filter(category=category_id).order_by('price')
        elif sort == 'count':
            # 人气排序
            goods_list = GoodsSKU.objects.filter(category=category_id).order_by('-sale_count')
        else:
            # 默认排序
            sort = 'default'
            goods_list = GoodsSKU.objects.filter(category=category_id).order_by('-SKU_id')

        # 分页
        paginator = Paginator(goods_list, 3)
        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1
        # 获取第page页的Page实例对象
        goods_page = paginator.page(page)

        # 页码控制，最多显示5页
        total_page_nums = paginator.num_pages
        # 1.总页数小于5页，显示所有页
        if total_page_nums < 5:
            pages = range(1, total_page_nums+1)
        # 2.当前页是前三页，显示前五页
        elif page <= 3:
            pages = range(1, 6)
        # 3.当前页是后三页，显示后五页
        elif total_page_nums - page < 3:
            pages = range(total_page_nums-4, total_page_nums+1)
        # 4.显示当前页前两页和后两页
        else:
            pages = range(page-2, page+3)

        # 获取购物车数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            con = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = con.hlen(cart_key)

        context = {'category': category,
                   'category_id': category_id,
                   'new_goods': new_goods,
                   'goods_list': goods_list,
                   'goods_page': goods_page,
                   'pages': pages,
                   'cart_count': cart_count,
                   'sort': sort}

        return render(request, 'list.html', context)
