# -*- coding: utf-8 -*-
"""示例 Django models —— chartflow v1 的 ER 抽取源(图书借阅域)。

本文件只是“数据标本”,不需要 Django 环境,不会被 import。
它是 ER 抽取的**源头真相**:er.json 由 LLM 依本文件手工抽取(v1),
校验在契约层做 —— 数据与模型不一致时,人审 er.json 比审图便宜。
"""
from django.db import models


class Category(models.Model):
    """图书分类(关系“拥有”的一侧)"""
    name = models.CharField("分类名", max_length=50)

    class Meta:
        verbose_name = "图书分类"
        verbose_name_plural = "图书分类"

    def __str__(self):
        return self.name


class Book(models.Model):
    """图书"""
    category = models.ForeignKey(Category, verbose_name="分类",
                                 on_delete=models.PROTECT)
    title = models.CharField("书名", max_length=200)
    author = models.CharField("作者", max_length=100)
    isbn = models.CharField("ISBN", max_length=20)
    total = models.PositiveIntegerField("馆藏总量", default=1)

    class Meta:
        verbose_name = "图书"
        verbose_name_plural = "图书"

    def __str__(self):
        return self.title


class Reader(models.Model):
    """读者"""
    card_no = models.CharField("借书证号", max_length=30, unique=True)
    name = models.CharField("姓名", max_length=50)
    # 概念上是多值属性:一个读者可登记多个号码,以逗号分隔(实现时宜拆表)
    phone = models.CharField("联系电话", max_length=200, blank=True)
    birth_date = models.DateField("出生日期", null=True, blank=True)

    class Meta:
        verbose_name = "读者"
        verbose_name_plural = "读者"

    def __str__(self):
        return self.name


class BorrowRecord(models.Model):
    """借阅记录(图书—读者的多侧)"""
    book = models.ForeignKey(Book, verbose_name="图书",
                             on_delete=models.CASCADE)
    reader = models.ForeignKey(Reader, verbose_name="读者",
                               on_delete=models.CASCADE)
    borrow_date = models.DateField("借出日期", auto_now_add=True)
    due_date = models.DateField("应还日期")
    returned = models.BooleanField("是否归还", default=False)

    class Meta:
        verbose_name = "借阅记录"
        verbose_name_plural = "借阅记录"

    def __str__(self):
        return f"{self.reader} × {self.book}"
