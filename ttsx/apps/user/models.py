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


class AddressManager(models.Manager):
    """地址模型管理器类"""
    # 1.改变原有查询的结果集：all()
    # 2.封装方法：用于操作模型类对应的数据表（增删改查）
    def get_default_address(self, user):
        """获取用户默认收货地址"""
        try:
            default_address = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:
            default_address = None

        return default_address


class Address(BaseModel):
    """地址表"""
    user = models.ForeignKey(User, verbose_name='所属用户', on_delete=models.CASCADE)
    receiver = models.CharField(max_length=20, verbose_name='收件人')
    receiver_addr = models.CharField(max_length=120, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, verbose_name='邮编')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')
    # 自定义一个模型管理器对象
    objects = AddressManager()

    class Meta:
        db_table = 'address'
        verbose_name = '地址信息'
        verbose_name_plural = verbose_name
