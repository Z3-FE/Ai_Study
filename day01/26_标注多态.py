class Animal:
    def make_sound(self):
        # 父类提供一个默认的或抽象的行为
        raise NotImplementedError("Subclass must implement abstract method")

class Dog(Animal):
    def make_sound(self):
        # 子类重写方法，提供自己的实现
        return "汪汪!"

class Cat(Animal):
    def make_sound(self):
        # 另一个子类提供不同的实现
        return "喵喵~"

# 定义一个统一的函数接口
def hear_sound(animal: Animal):
    """这个函数不关心传入的对象是 Dog 还是 Cat，只关心它有没有 make_sound 方法"""
    print(f"听到了: {animal.make_sound()}")

# 统一的接口调用不同的实现
dog = Dog()
cat = Cat()

hear_sound(dog) # 传入 Dog 对象，调用 Dog 的 make_sound
# 输出: 听到了: 汪汪!

hear_sound(cat) # 传入 Cat 对象，调用 Cat 的 make_sound
# 输出: 听到了: 喵喵~