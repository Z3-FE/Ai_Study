# 原始数据
data_list = [10, 5, 20, 15]
data_tuple = (1, 0, 'hello', [])  # 包含真值和假值
data_set = {30, 40}
data_dict = {'a': 1, 'b': 2}

print("=" * 50)
print("       Python 常用内置函数演示")
print("=" * 50)

# ----------------------------------------------------
# 1. 类型转换与构造函数
# ----------------------------------------------------
print("\n--- 1. 类型转换与构造 ---")

# a. 基本类型转换
integer_val = int("123")
float_val = float("3.14")
string_val = str(100)
boolean_val = bool(data_tuple)  # 转换为 True (非空元组)
print(f"int('123'): {integer_val}, type: {type(integer_val)}")
print(f"bool((...)): {boolean_val}")

# b. 序列构造
new_list = list(data_tuple)
new_set = set(data_list + [10])  # 用于去重
new_dict = dict([('x', 99), ('y', 88)])
print(f"list(tuple): {new_list}")
print(f"set(list) (去重): {new_set}")
print(f"dict(kv_pairs): {new_dict}")

# ----------------------------------------------------
# 2. 序列和容器操作
# ----------------------------------------------------
print("\n--- 2. 序列和容器操作 ---")

# a. 长度、最大/最小、求和
print(f"len(list): {len(data_list)}")
print(f"max(list): {max(data_list)}")
print(f"sum(list): {sum(data_list)}")

# b. 排序
sorted_list = sorted(data_list, reverse=True)
print(f"sorted(list, reverse=True): {sorted_list}")

# c. 迭代工具
print("range(), enumerate(), zip() 示例:")
for i in range(2, 5):  # 从 2 开始，到 5 之前结束
    print(f"  range输出: {i}")

for index, value in enumerate(data_list):
    if index < 2:
        print(f"  enumerate输出: 索引 {index}, 值 {value}")

keys = ['A', 'B', 'C']
values = [1, 2, 3]
zipped = list(zip(keys, values))
print(f"  zip(keys, values): {zipped}")

# ----------------------------------------------------
# 3. 数学和逻辑运算
# ----------------------------------------------------
print("\n--- 3. 数学和逻辑运算 ---")

# a. 数学运算
print(f"abs(-5): {abs(-5)}")
print(f"round(3.14159, 2): {round(3.14159, 2)}")

# b. 逻辑判断
all_true = [1, 5, True]
all_false = [1, 0, True]
print(f"all([1, 5, True]): {all(all_true)}")  # True
print(f"any([1, 0, True]): {any(all_false)}")  # True (因为有 1 和 True)

# ----------------------------------------------------
# 4. 高级工具和反射
# ----------------------------------------------------
print("\n--- 4. 高级工具和反射 ---")


class MyClass:
    pass


instance = MyClass()
print(f"isinstance(instance, MyClass): {isinstance(instance, MyClass)}")
print(f"type(instance): {type(instance)}")
print(f"type('abc'): {type('abc')}")

# print() 和 input() 是最常用的内置函数，此处仅作提及
# print("--- 结束 ---")
# input("按 Enter 键退出...")