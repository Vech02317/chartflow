# -*- coding: utf-8 -*-
"""活动模块 —— 校园活动报名系统样例的 app: activity"""
from django.db import models

from accounts.models import User


class ActivityCategory(models.Model):
    """活动分类。"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建人")
    name = models.CharField("分类名", max_length=32)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)


class Activity(models.Model):
    """活动。"""

    category = models.ForeignKey(ActivityCategory, on_delete=models.PROTECT,
                                 verbose_name="所属分类")
    creator = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name="created_activities", verbose_name="发起人")
    title = models.CharField("活动名称", max_length=128)
    description = models.TextField("活动简介")
    start_at = models.DateTimeField("开始时间")
    end_at = models.DateTimeField("结束时间")
    capacity = models.IntegerField("名额上限")
    status = models.CharField("状态", max_length=16, default="draft")
    cover = models.ImageField("封面图", upload_to="covers/", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)


class Enrollment(models.Model):
    """报名记录。"""

    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, verbose_name="活动")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="报名人")
    venue_slot = models.ForeignKey("venue.VenueSlot", null=True, blank=True,
                                   on_delete=models.SET_NULL, verbose_name="使用时段")
    status = models.CharField("报名状态", max_length=16, default="pending")
    attended = models.BooleanField("是否签到", default=False)
    created_at = models.DateTimeField("报名时间", auto_now_add=True)


class ActivityReview(models.Model):
    """活动评价。"""

    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, verbose_name="活动")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="评价人")
    score = models.PositiveSmallIntegerField("评分")
    comment = models.TextField("评价内容", blank=True)
    created_at = models.DateTimeField("评价时间", auto_now_add=True)


class ActivityTag(models.Model):
    """活动标签。"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建人")
    name = models.CharField("标签名", max_length=16)
    activities = models.ManyToManyField(Activity, verbose_name="标记的活动")
