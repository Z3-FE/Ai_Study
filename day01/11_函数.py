# 基础函数
def weight(age = 1, weight = 2):
    return age * weight

print(weight(3,2))
print(weight(3,4))
print(weight(3,6))
print(weight())


print("*********限制传参方式**************")

def info_data(name, /, *, age, sex):
    print(f'你的名字: {name}, 年龄：{age} , 性别：{sex}')


# / 限制name必须是位置参数  （位置参数：直接在当前位置传入就行）
# * 限制age必须是关键字参数  （关键字参数：使用函数方法中的入参名称来进行赋值）
info_data('张三',age=15, sex='男')

print('**********可变参数**********************')

def info_data2(name, *args, **kwargs):
    print(f'你的名字{name}')
    print(f'args{args}')
    print(f'args中喝酒的index位置{args.index('喝酒')}')
    print(f'kwargs{kwargs}')
    print(f'kwargs中age的值{kwargs.get("age")}')
# *args 接收位置参数 ('抽烟', '喝酒', '烫头')
# **kwargs 关键字参数 {'age': 15, 'sex': '男'}  也叫 字典
info_data2('李四', '抽烟', '喝酒', '烫头', age=15, sex='男')

print('**************函数参数说明文档**************')

def info_data3(name, age):
    """
    输出你的名字和年龄
    :param name: 名字
    :param age: 年龄
    :return:
    """
    print(f'你的名字{name}')
    print(f'age{age}')