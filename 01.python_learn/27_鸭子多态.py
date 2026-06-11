# 无需继承，只要对象具有相同的方法名，即可实现多态。
class Car:
    def move(self):
        return "汽车在道路上行驶"

class Boat:
    def move(self):
        return "船只在水面上航行"

class Drone:
    # 尽管 Drone 和 Car/Boat 无继承关系，但它也实现了 move()
    def move(self):
        return "无人机在空中飞行"

# 统一的接口函数
def transport(vehicle):
    """这个函数只要求 vehicle 对象实现 move() 方法"""
    print(f"交通工具正在移动: {vehicle.move()}")

# 统一的接口调用，实现了对不同对象的处理
transport(Car())
# 输出: 交通工具正在移动: 汽车在道路上行驶

transport(Boat())
# 输出: 交通工具正在移动: 船只在水面上航行

transport(Drone())
# 输出: 交通工具正在移动: 无人机在空中飞行