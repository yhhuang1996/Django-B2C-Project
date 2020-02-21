from django.db import models
from db.base_model import BaseModel
from django.contrib.auth.models import AbstractUser
# Create your models here.


class User(AbstractUser, BaseModel):
    """用户表"""

    class Meta:
        db_table = 'User'
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name


class Address(BaseModel):
    """地址表"""
    user = models.ForeignKey(User, verbose_name='所属用户', on_delete=models.CASCADE)
    receiver = models.CharField(max_length=20, verbose_name='收件人')
    receive_addr = models.CharField(max_length=120, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, verbose_name='邮编')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')

    class Meta:
        db_table = 'address'
        verbose_name = '地址信息'
        verbose_name_plural = verbose_name
