from django.shortcuts import render, redirect
from django.urls import reverse
import re
from apps.user.models import *
from django.http import HttpResponse
from django.views.generic import View
from django.conf import settings
from django.core.mail import send_mail
from itsdangerous import TimedJSONWebSignatureSerializer as Scrt
from itsdangerous import SignatureExpired
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django_redis import get_redis_connection
from apps.goods.models import *


# Create your views here.


class RegisterView(View):
    """注册"""

    def get(self, request):
        """显示注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """进行注册处理"""
        # 1.接收数据
        username = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        check_pwd = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 2.进行数据校验
        if not all([username, pwd, email]):  # all方法中传可迭代对象，对每个元素进行判断，所有为真，返回真
            # 数据不完整
            return render(request, 'register.html', {'error_msg': '数据不完整'})

        if pwd != check_pwd:
            # 密码不一致
            return render(request, 'register.html', {'error_msg': '两次输入的密码不一致'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            # 邮箱不合法
            return render(request, 'register.html', {'error_msg': '邮箱不合法'})

        # 校验是否勾选协议
        if allow != 'on':
            # 未勾选协议
            return render(request, 'register.html', {'error_msg': '请同意协议'})

        # 校验用户名是否重复
        try:
            check_username = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在，合法
            check_username = None

        if check_username:
            # 用户名重复
            return render(request, 'register.html', {'error_msg': '用户名重复'})

        # 3.进行业务处理：用户注册
        user = User.objects.create_user(username, email, pwd)
        user.is_active = 0
        user.save()

        # 发送激活邮件，包含激活链接：http://127.0.0.1:8000/user/active/3
        # 激活链接中需要包含用户的身份信息，且需要加密
        # 加密用户的身份信息，生成的token
        scrt = Scrt(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = scrt.dumps(info)
        # 将bytes格式的token解码为str
        token = token.decode()

        # 发邮件
        send_register_active_email.delay(email, username, token)

        # 4.返回应答，跳转到首页
        return redirect(reverse('user:login'))


class Active(View):
    """用户激活"""

    def get(self, request, token):
        # 进行解密，获取要激活的用户信息
        scrt = Scrt(settings.SECRET_KEY, 3600)
        try:
            info = scrt.loads(token)
            # 获取待激活用户的id
            user_id = info['confirm']
            # 根据用户id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')


# /user/login
class Login(View):
    """登录"""

    def get(self, request):
        """显示登录页面"""
        if 'username' in request.COOKIES:
            username = request.COOKIES['username']
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        """登录校验"""
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')

        # 检验数据
        if not all([username, password]):
            return render(request, 'login.html', {'error_msg': '数据不完整'})

        # 业务处理：登录校验
        user = authenticate(request, username=username, password=password)
        print(user, password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 用户已激活，记录用户登录状态
                login(request, user)

                # 获取登录后要跳转的地址
                next_url = request.GET.get('next', reverse('goods:index'))
                response = redirect(next_url)

                # 判断是否记住用户名
                if remember == 'on':
                    response.set_cookie('username', username)
                else:
                    response.delete_cookie('username')
                # 跳转到首页
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'error_msg': '用户名未激活'})

        else:
            # 用户名或密码错误
            return render(request, 'login.html', {'error_msg': '用户名或密码错误'})


# /user/logout
class Logout(View):
    """退出登录"""

    def get(self, request):
        # 清除用户的session信息
        logout(request)
        return redirect(reverse('goods:index'))


# /user
class UserInfo(LoginRequiredMixin, View):
    """用户中心-信息页"""

    # login_url = '/user/register'  若用户未登录，优先跳转地址，不设置则去settings文件中找LOGIN_URL
    def get(self, request):
        # 获取用户个人信息
        user = request.user
        addr = Address.objects.get_default_address(user)
        # 获取用户的历史浏览记录
        con = get_redis_connection('default')
        history_key = 'history_%d' % user.id

        # 获取用户最新浏览的5个商品id
        sku_ids = con.lrange(history_key, 0, 4)

        # 遍历获取用户浏览的商品信息
        goods_li = []
        for sku_id in sku_ids:
            goods = GoodsSKU.objects.get(id=sku_id)
            goods_li.append(goods)

        # 组织上下文
        context = {'page': 'user', 'addr': addr, 'goods_li': goods_li}
        # request.user.is_authenticated()
        # Django框架会把request.user自动传给模板文件
        return render(request, 'user_center_info.html', context)


# user/order/
class UserOrder(LoginRequiredMixin, View):
    """用户中心-订单页"""

    def get(self, request):
        # 获取用户的订单信息
        return render(request, 'user_center_order.html', {'page': 'order'})


# /user/address/
class UserAddress(LoginRequiredMixin, View):
    """用户中心-地址页"""

    def get(self, request):
        user = request.user
        # 获取用户的默认收货地址
        default_address = Address.objects.get_default_address(user)
        return render(request, 'user_center_site.html', {'page': 'address', 'address': default_address})

    def post(self, request):
        """新建地址"""
        # 接收数据
        receiver = request.POST.get('receiver')
        address = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据
        if not all([receiver, address, phone]):
            return render(request, 'user_center_site.html', {'error_msg': '数据不完整'})

        # 校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'error_msg': '手机号格式有误'})

        # 业务处理：地址添加
        # 如果用户已存在默认收货地址，添加地址不作为默认收货地址，否则作为默认收货地址
        # 获取当前登录用户对应的user对象
        user = request.user

        if Address.objects.get_default_address(user):
            is_default = False
        else:
            is_default = True

        # 添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               receiver_addr=address,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default
                               )

        # 返回应答，get请求
        return redirect(reverse('user:address'))
