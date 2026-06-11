class Person:
    def __init__(self, name, age):
        self._name = name  # 使用单下划线作为内部约定
        self._age = None  # 先初始化内部私有属性
        self.age = age  # 调用 Setter 设置初始值，保证验证逻辑运行

    # ------------------------------------
    # 1. Getter (获取器)
    # ------------------------------------
    @property
    def age(self):
        """定义 age 的 Getter 方法"""
        print("-> 正在获取 age...")
        return self._age

    # ------------------------------------
    # 2. Setter (设置器)
    # ------------------------------------
    @age.setter
    def age(self, new_age):
        """定义 age 的 Setter 方法"""
        print("-> 正在设置 age...")
        if not isinstance(new_age, int) or new_age <= 0:
            raise ValueError("年龄必须是正整数！")
        self._age = new_age

    # 3. Deleter (删除器 - 较少用)
    @age.deleter
    def age(self):
        """定义 age 的 Deleter 方法"""
        print("-> 正在删除 age...")
        del self._age

    @property
    def name(self):
        """Name 属性只提供 Getter，实现只读"""
        return self._name


# ------------------------------------
# 外部调用
# ------------------------------------
p = Person("Bob", 30)

# 1. 访问 (调用 Getter)
print(f"当前年龄: {p.age}")

# 2. 设置 (调用 Setter)
p.age = 31
print(f"新年龄: {p.age}")

# 3. 验证失败 (Setter 阻止非法值)
try:
    p.age = -5
except ValueError as e:
    print(f"设置失败: {e}")

# 4. 只读属性 (Name 没有定义 Setter)
print(f"姓名: {p.name}")
try:
    p.name = "Alice"
except AttributeError as e:
    print(f"设置失败: {e}")  # 抛出错误