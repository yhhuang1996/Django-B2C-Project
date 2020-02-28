from django.contrib import admin
from apps.goods.models import *
from django.core.cache import cache
# Register your models here.


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """新增或更新表中数据时调用"""
        super().save_model(request, obj, form, change)

        # 发出任务让celery worker重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页缓存
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        """删除表中数据时调用"""
        super().delete_model(request, obj)
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页缓存
        cache.delete('index_page_data')


class GoodsSKUAdmin(BaseModelAdmin):
    list_display = ['goodsSPU', 'SKU_id', 'name', 'category', 'price', 'unit', 'stock', ]


class GoodsSPUAdmin(BaseModelAdmin):
    list_display = ['SPU_id', 'name']


class GoodsImageAdmin(BaseModelAdmin):
    list_display = ['goodsSKU', 'image']


class GoodsCategoryAdmin(BaseModelAdmin):
    list_display = ['name']


class IndexGoodsCategoryAdmin(BaseModelAdmin):
    pass


class IndexSlideAdmin(BaseModelAdmin):
    list_display = ['goodsSKU']


class IndexPromotionAdmin(BaseModelAdmin):
    list_display = ['name']


admin.site.register(GoodsSKU, GoodsSKUAdmin)
admin.site.register(GoodsSPU, GoodsSPUAdmin)
admin.site.register(GoodsImage, GoodsImageAdmin)
admin.site.register(GoodsCategory, GoodsCategoryAdmin)
admin.site.register(IndexGoodsCategory, IndexGoodsCategoryAdmin)
admin.site.register(IndexSlide, IndexSlideAdmin)
admin.site.register(IndexPromotion, IndexPromotionAdmin)
