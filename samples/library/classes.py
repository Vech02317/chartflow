# -*- coding: utf-8 -*-
"""示例类结构 —— 类图抽取源(图书借阅域)。仅数据标本,不需要运行环境。"""


class Person:
    """人员(抽象基类)"""
    name: str
    phone: str

    def contact(self) -> str: ...


class Reader(Person):
    """读者"""
    card_no: str
    credit: int

    def borrow(self, item): ...
    def give_back(self, loan): ...


class Librarian(Person):
    """图书管理员"""
    employee_no: str

    def register_item(self, item): ...
    def handle_overdue(self, loan): ...


class Item:
    """馆藏项(抽象)"""
    title: str
    isbn: str
    total: int

    def available_count(self) -> int: ...


class Book(Item):
    """图书"""
    author: str
    publisher: str


class Magazine(Item):
    """期刊"""
    issue: str


class Loan:
    """借阅单"""
    borrow_date: str
    due_date: str
    returned: bool

    def overdue_days(self) -> int: ...


class FineCalculator:
    """罚金计算器(工具类,被 Library 在方法内调用)"""
    rate: float

    def compute(self, loan): ...


class Library:
    """图书馆(聚合馆藏、组合借阅单)"""
    name: str

    def add_item(self, item): ...
    def lend(self, reader: Reader, item: Item): ...
    def settle(self, loan: Loan): ...
