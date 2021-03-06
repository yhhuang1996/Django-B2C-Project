# Generated by Django 3.0.3 on 2020-03-04 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_auto_20200228_1623'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderinfo',
            name='total_pay',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='总支付金额'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='orderinfo',
            name='total_price',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='总商品金额'),
        ),
        migrations.AlterField(
            model_name='orderinfo',
            name='trade_num',
            field=models.CharField(default='', max_length=128, verbose_name='支付编号'),
        ),
    ]
