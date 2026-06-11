
class Person:

    # 类属性          公共数据
    max_age = 120
    plant = '地球'


    # 构造函数 self = 自身实例
    # 实例属性
    def __init__(self, name, job, age):
        self.name = name
        self.job = job
        #限制年龄的最大值
        if age <= Person.max_age:
            self.age = age
        else:
            self.age = Person.max_age
            # Person.max_age == self.max_age
            print(f'超出了最大年龄：{Person.max_age}, {self.max_age}')
    # 实例方法
    def speak(self, message):
        print(f'我叫：{self.name},工作：{self.job},年龄：{self.age}，我想说：{message}')
    
    # 类方法
    # cls 就是类
    @classmethod
    def change_max_age(cls, new_age):
        cls.max_age = new_age
    # 工厂模式 （接收不同类型的数据，直至符合调用）
    @classmethod
    def create(cls, info_str):
        name, job, age = info_str.split('-')
        return cls(name, job, int(age))

    # 静态方法
    # 通常定义为工具方法
    @staticmethod
    def msk_Name(name):
        return name[0:1] + '*' + name[2:]


p1 = Person("Jane", "Developer", 22)
p2 = Person("李四", "抽烟", 124)

print(p1.name, p1.job, p1.age)
print(p2.name, p2.job, p2.age)

# 外部添加属性
p1.address = '天津大麻花'
# 整体打印
print(p1.__dict__)
print(p2.__dict__)
# 实例可以访问类属性
# 类型判断
# 类上有自定义的方法，但是实例对象上没有，但是实例对象可以直接调用

def speakNew():
    print('NEW,NEW,NEW,NEW,NEW,NEW,NEW,NEW,NEW,NEW,NEW,NEW,NEW,NEW,')
    
p1.speak = speakNew
p1.speak()
p2.speak('俺是大信球')
print(p1.max_age)
print(p1.__dict__) #可以重写 类中的方法
print(p2.__dict__) # 不会展示 类中的方法
print(Person.__dict__)

# 注： 类也能直接调用自身实例方法，但是不推荐
Person.speak(p2,'我嫩爹')

# 类调用类方法
Person.change_max_age(130)
print(Person.max_age)

# 工厂模式： 类创建实例
p3 = Person.create('迪丽热巴-演员-18')
print(p3.__dict__)

# 静态方法调用
print(p3.msk_Name(p3.name))
