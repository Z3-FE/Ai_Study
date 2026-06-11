"""
在 Python 中，抽象类 (Abstract Class) 是一种不能被直接实例化（创建对象）的类，
其主要目的是作为基类，为子类提供统一的接口定义和骨架。
抽象类中通常包含抽象方法 (Abstract Method)，
这些方法必须由任何继承自该抽象类的子类来实现。
"""

from abc import ABC, abstractmethod

# 1. 定义抽象基类
class Shape(ABC):
    """几何图形抽象类"""

    @abstractmethod
    def area(self):
        """抽象方法：计算面积，所有子类必须实现此方法"""
        pass # 抽象方法通常只包含 pass

    @abstractmethod
    def perimeter(self):
        """抽象方法：计算周长，所有子类必须实现此方法"""
        pass

    def description(self):
        """普通方法：抽象类中也可以包含已实现的方法"""
        return "这是一个几何图形，具有面积和周长属性。"

# 2. 尝试实例化抽象类 (会失败)
try:
    s = Shape()
except TypeError as e:
    print(f"❌ 实例化抽象类失败: {e}")
    # 错误提示: Can't instantiate abstract class Shape with abstract methods area, perimeter

# 3. 定义具体子类 (未实现全部抽象方法)
class PartialCircle(Shape):
    # 故意只实现 area()
    def area(self):
        return 3.14 * (5**2)

# 4. 尝试实例化不完整的子类 (会失败)
try:
    pc = PartialCircle()
except TypeError as e:
    print(f"❌ 实例化不完整的子类失败: {e}")
    # 错误提示: Can't instantiate abstract class PartialCircle with abstract methods perimeter

# 5. 定义完整子类 (必须实现全部抽象方法)
class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        """实现抽象方法 area"""
        return self.width * self.height

    def perimeter(self):
        """实现抽象方法 perimeter"""
        return 2 * (self.width + self.height)

# 6. 实例化完整的子类 (成功)
r = Rectangle(10, 5)
print("\n✅ 实例化完整子类成功:")
print(f"  矩形面积: {r.area()}")
print(f"  矩形周长: {r.perimeter()}")
print(f"  调用抽象类中的普通方法: {r.description()}")

