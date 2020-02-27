# 使用celery
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import os
import django
from django.template import loader

# 在任务处理者一端加一下两句，环境初始化
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ttsx.settings')
django.setup()

from apps.goods.models import *

# 创建一个Celery实例对象
app = Celery('celery_tasks.tasks', broker=settings.CELERY_BROKER_REDIS)


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    """发送激活邮件"""
    subject = "天天生鲜欢迎信息"
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = "<h1>欢迎%s，恭喜您成为天天生鲜会员</h1>请点击以下链接激活<br>%s%s" % (settings.CELERY_EMAIL_TASKS_URL, username, token)

    send_mail(subject, message, sender, receiver, html_message=html_message)


@app.task
def generate_static_index_html():
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

    # 组织上下文
    context = {'category': category,  # 新鲜水果、猪牛羊肉、家禽蛋类...集合
               'slide': slide,
               'promotion': promotion,
               }

    # 1.加载模板文件，返回模板对象
    temp = loader.get_template('static_index.html')
    # # 2.定义模板上下文
    # context = RequestContext(request, context)
    # 3.渲染文件
    static_index_html = temp.render(context)

    # 生成首页对应的静态文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)
