from django.shortcuts import render, redirect
from django.urls import reverse
import re
from apps.user.models import User
from django.http import HttpResponse
from django.views.generic import View
from django.conf import settings
from django.core.mail import send_mail
from itsdangerous import TimedJSONWebSignatureSerializer as Scrt
from itsdangerous import SignatureExpired

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
        print(username)
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
        subject = "天天生鲜欢迎信息"
        message = ''
        sender = settings.EMAIL_FROM
        receiver = [email]
        html_message = "<h1>欢迎%s，恭喜您成为天天生鲜会员</h1>请点击以下链接激活<br>http://127.0.0.1:8000/user/active/%s" % (username, token)

        send_mail(subject, message, sender, receiver, html_message=html_message)

        # 4.返回应答，跳转到首页
        return redirect(reverse('goods:index'))


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
        return render(request, 'login.html')