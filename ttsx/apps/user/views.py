from django.shortcuts import render, redirect
from django.urls import reverse
import re
from apps.user.models import User
from django.views.generic import View
# Create your views here.


# /user/register
def register(request):
    """显示注册页面"""
    if request.method == "GET":
        # 显示注册页面
        return render(request, 'register.html')
    else:
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

        # 4.返回应答，跳转到首页
        return redirect(reverse('goods:index'))


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

        # 4.返回应答，跳转到首页
        return redirect(reverse('goods:index'))