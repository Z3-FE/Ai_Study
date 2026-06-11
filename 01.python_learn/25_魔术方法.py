class Book:
    """
    演示 Python 中最常用的魔术方法 (Dunder Methods)。
    """
    def __init__(self, title, author, pages):
        """
        1. __init__: 初始化方法。
           在对象被创建后立即调用，用于设置对象的初始状态（属性）。
        """
        self.title = title
        self.author = author
        self.pages = pages
        self.chapters = 0

    def __str__(self):
        """
        2. __str__: 字符串表示方法（用户友好）。
           当使用 print(obj) 或 str(obj) 时被调用。
        """
        return f"《{self.title}》 作者: {self.author}, 页数: {self.pages}"

    def __repr__(self):
        """
        3. __repr__: 官方字符串表示方法（面向开发者）。
           用于调试和日志记录，输出通常应能重现对象。
        """
        return f"Book(title='{self.title}', author='{self.author}', pages={self.pages})"

    def __len__(self):
        """
        4. __len__: 长度方法。
           当使用内置函数 len(obj) 时被调用。
           在这里，我们让 len() 返回书的页数。
        """
        return self.pages

    def __add__(self, other):
        """
        5. __add__: 加法运算符重载。
           定义对象之间使用 '+' 运算符时的行为。
           在这里，我们实现两本书页数相加。
        """
        if isinstance(other, Book):
            # 如果是另一本书，返回页数总和
            return self.pages + other.pages
        elif isinstance(other, int):
            # 如果是整数，返回页数加上整数
            return self.pages + other
        else:
            # 兼容其他类型
            return NotImplemented


# ----------------------------------------------------
# 测试和验证
# ----------------------------------------------------
print("=" * 40)
print("             魔术方法演示")
print("=" * 40)

# 实例化对象 (触发 __init__)
book1 = Book("Python 编程", "Guido", 500)
book2 = Book("AI 大模型", "GPT", 350)


# 1. __str__ (用户友好输出)
print("\n1. __str__ (使用 print):")
print(book1)
# 预期输出: 《Python 编程》 作者: Guido, 页数: 500


# 2. __repr__ (开发者调试输出)
print("\n2. __repr__ (使用 repr 或交互式环境):")
print(repr(book2))
# 预期输出: Book(title='AI 大模型', author='GPT', pages=350)


# 3. __len__ (长度计算)
print("\n3. __len__ (使用 len()):")
print(f"《{book1.title}》的页数: {len(book1)}")
# 预期输出: 500


# 4. __add__ (运算符重载)
print("\n4. __add__ (使用 + 运算符):")
# 两本书页数相加
total_pages = book1 + book2
print(f"两本书总页数: {total_pages}")
# 预期输出: 850 (500 + 350)

# 书本页数加上整数
pages_plus_bonus = book1 + 50
print(f"书本页数加 50: {pages_plus_bonus}")
# 预期输出: 550 (500 + 50)