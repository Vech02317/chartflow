# -*- coding: utf-8 -*-
"""场地模块 —— 校园活动报名系统样例的 app: venue"""
from django.db import models

from accounts.models import User


class Venue(models.Model):
    """场地。"""

    applicant = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="申请人")
    name = models.CharField("场地名称", max_length=64)
    location = models.CharField("位置", max_length=128)
    capacity = models.IntegerField("容纳人数")
    is_open = models.BooleanField("是否开放", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)


class VenueSlot(models.Model):
    """场地时段。"""

    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, verbose_name="所属场地")
    start_at = models.DateTimeField("开始时间")
    end_at = models.DateTimeField("结束时间")
    is_booked = models.BooleanField("是否已约", default=False)


class VenueBooking(models.Model):
    """场地预约。"""

    slot = models.ForeignKey(VenueSlot, on_delete=models.CASCADE, verbose_name="预约时段")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="预约人")
    purpose = models.CharField("用途", max_length=128)
    status = models.CharField("预约状态", max_length=16, default="pending")
    created_at = models.DateTimeField("预约时间", auto_now_add=True)


class VenueReview(models.Model):
    """场地评价。"""

    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, verbose_name="场地")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="评价人")
    score = models.PositiveSmallIntegerField("评分")
    comment = models.TextField("评价内容", blank=True)
    created_at = models.DateTimeField("评价时间", auto_now_add=True)


class VenueEquipment(models.Model):
    """场地设备。"""

    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, verbose_name="所属场地")
    activity = models.ForeignKey("activity.Activity", null=True, blank=True,
                                 on_delete=models.SET_NULL, verbose_name="配备的活动")
    name = models.CharField("设备名", max_length=64)
    quantity = models.IntegerField("数量", default=1)
