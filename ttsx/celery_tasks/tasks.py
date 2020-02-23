# 使用celery
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import time


# 创建一个Celery实例对象
app = Celery('celery_tasks.tasks', broker='redis://172.17.0.10:6379/8')


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    """发送激活邮件"""
    subject = "天天生鲜欢迎信息"
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = "<h1>欢迎%s，恭喜您成为天天生鲜会员</h1>请点击以下链接激活<br>http://127.0.0.1:8000/user/active/%s" % (username, token)

    send_mail(subject, message, sender, receiver, html_message=html_message)
