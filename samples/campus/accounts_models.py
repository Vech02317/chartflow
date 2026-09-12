# -*- coding: utf-8 -*-
"""账户模块 —— 校园活动报名系统样例的 app: accounts

本样例演示**按模块拆 ER 图**。三个 app 各一个文件,是刻意的:
模块边界取源码的 app 名,一眼可见、可对着文件核。
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """用户。继承 AbstractUser,父类字段已并入本实体。"""

    nickname = models.CharField("昵称", max_length=32, blank=True)
    avatar = models.ImageField("头像", upload_to="avatars/", blank=True)
    student_no = models.CharField("学号", max_length=20, unique=True)
    college = models.CharField("学院", max_length=64, blank=True)
    credit = models.IntegerField("信用分", default=100)
    is_banned = models.BooleanField("是否封禁", default=False)


class Notification(models.Model):
    """站内通知。"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="接收人")
    title = models.CharField("标题", max_length=128)
    content = models.TextField("内容")
    is_read = models.BooleanField("是否已读", default=False)
    created_at = models.DateTimeField("发送时间", auto_now_add=True)


class LoginLog(models.Model):
    """登录日志。"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    ip = models.GenericIPAddressField("登录IP")
    device = models.CharField("设备", max_length=128, blank=True)
    created_at = models.DateTimeField("登录时间", auto_now_add=True)
