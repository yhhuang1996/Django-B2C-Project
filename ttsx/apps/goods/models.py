from django.db import models
from db.base_model import BaseModel
from tinymce.models import HTMLField


# Create your models here.


class GoodsCategory(BaseModel):
    """商品种类模型类"""
    name = models.CharField(max_length=20, verbose_name='商品种类')
    logo = models.CharField(max_length=20, verbose_name='雪碧图标识')
    image = models.ImageField(upload_to='type', verbose_name='商品类型图片')

    class Meta:
        db_table = 'goods_category'
        verbose_name = '商品种类'
        verbose_name_plural = verbose_name


class GoodsSPU(BaseModel):
    """商品SPU模型类"""
    name = models.CharField(max_length=20, verbose_name='SPU_名称')
    # 富文本类型
    detail = HTMLField(blank=True, verbose_name='商品详情')

    class Meta:
        db_table = 'goods_SPU'
        verbose_name = '商品SPU'
        verbose_name_plural = verbose_name


class GoodsSKU(BaseModel):
    """商品SKU模型类"""
    is_on_sale_choice = (
        (0, '下架'),
        (1, '上架')
    )
    goodsSPU = models.ForeignKey(GoodsSPU, verbose_name='SPU_ID', on_delete=models.CASCADE)
    category = models.ForeignKey(GoodsCategory, verbose_name='种类', on_delete=models.CASCADE)
    name = models.CharField(max_length=120, verbose_name='商品名称')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='价格')
    unit = models.CharField(max_length=20, verbose_name='单位')
    stock = models.IntegerField(default=0, verbose_name='库存')
    image = models.ImageField(upload_to='goods', verbose_name='商品图片')
    short_info = models.CharField(max_length=256, verbose_name='商品简介')
    sale_count = models.IntegerField(default=0, verbose_name='销量')
    is_on_sale = models.SmallIntegerField(default=1, choices=is_on_sale_choice, verbose_name='是否上架')

    class Meta:
        db_table = 'goods_SKU'
        verbose_name = '商品SKU'
        verbose_name_plural = verbose_name


class GoodsImage(BaseModel):
    """商品图片模型类"""
    goodsSKU = models.ForeignKey(GoodsSKU, verbose_name='商品SKU', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='', verbose_name='商品图片')

    class Meta:
        db_table = 'goods_images'
        verbose_name = '商品图片'
        verbose_name_plural = verbose_name


class IndexSlide(BaseModel):
    """首页轮播商品模型类"""
    goodsSKU = models.ForeignKey(GoodsSKU, verbose_name='商品SKU', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='banner', verbose_name='商品图片')
    index = models.SmallIntegerField(default=0, verbose_name='轮播顺序')

    class Meta:
        db_table = 'index_slide'
        verbose_name = '首页轮播商品'
        verbose_name_plural = verbose_name


class IndexPromotion(BaseModel):
    """首页促销商品模型类"""
    name = models.CharField(max_length=20, verbose_name='活动名称')
    image = models.ImageField(upload_to='banner', verbose_name='商品图片')
    url = models.URLField(verbose_name='活动页面链接')
    index = models.SmallIntegerField(default=0, verbose_name='排列顺序')

    class Meta:
        db_table = 'index_promotion'
        verbose_name = '首页促销商品'
        verbose_name_plural = verbose_name


class IndexCategory(BaseModel):
    """首页商品分类模型类"""
    show_method_choice = (
        (0, '文字'),
        (1, '图片')
    )
    goodsSKU = models.ForeignKey(GoodsSKU, verbose_name='商品SKU', on_delete=models.CASCADE)
    goods_category = models.ForeignKey(GoodsCategory, verbose_name='商品种类', on_delete=models.CASCADE)
    index = models.SmallIntegerField(default=0, verbose_name='排列顺序')
    show_method = models.BooleanField(default=0, choices=show_method_choice, verbose_name='展示方式')

    class Meta:
        db_table = 'index_category'
        verbose_name = '首页商品分类'
        verbose_name_plural = verbose_name
