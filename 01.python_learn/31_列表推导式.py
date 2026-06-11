# 原始数据
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
names = ["alice", "bob", "charlie", "david"]
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

print("=" * 50)
print("           Python 列表推导式演示")
print("=" * 50)


# ----------------------------------------------------
# 1. 基本映射 (Map)
# ----------------------------------------------------
# 目标: 将列表中的每个元素平方

squared_numbers = [x * x for x in numbers]
print("1. 基本映射 (平方):")
print(f"   原始列表: {numbers[:5]}...")
print(f"   结果:     {squared_numbers}")


# 目标: 将所有名字的首字母大写
capitalized_names = [name.capitalize() for name in names]
print("\n   字符串操作 (首字母大写):")
print(f"   原始列表: {names}")
print(f"   结果:     {capitalized_names}")


# ----------------------------------------------------
# 2. 带有筛选 (Filter)
# ----------------------------------------------------
# 目标: 筛选出大于 5 的偶数

filtered_and_processed = [
    x * 10                   # 结果
    for x in numbers         # 迭代 numbers 列表
    if x > 5 and x % 2 == 0  # 筛选条件：大于 5 且为偶数
]

print("\n2. 带有筛选 (Filter):")
print(f"   条件: 大于 5 的偶数 * 10")
print(f"   结果: {filtered_and_processed}")
# 结果应该是: [60, 80, 100]


# ----------------------------------------------------
# 3. 带有 If...Else 表达式
# ----------------------------------------------------
# 目标: 如果数字是偶数标记为 'Even'，否则标记为 'Odd'

if_else_result = [
    'Even' if x % 2 == 0 else 'Odd'
    for x in numbers[:5] # 只看前 5 个
]

print("\n3. 带有 If/Else 表达式:")
print(f"   结果: {if_else_result}")
# 结果应该是: ['Odd', 'Even', 'Odd', 'Even', 'Odd']


# ----------------------------------------------------
# 4. 嵌套推导式 (处理二维列表)
# ----------------------------------------------------
# 目标: 扁平化 (Flatten) 矩阵，将所有元素提取到一个单维列表

# 传统方法需要两层循环
# flattened_traditional = []
# for row in matrix:
#     for num in row:
#         flattened_traditional.append(num)

# 嵌套推导式
flattened_list = [
    num
    for row in matrix  # 外层循环：迭代每一行
    for num in row     # 内层循环：迭代行中的每一个数字
]

print("\n4. 嵌套推导式 (扁平化):")
print(f"   原始矩阵: {matrix}")
print(f"   结果:     {flattened_list}")
# 结果应该是: [1, 2, 3, 4, 5, 6, 7, 8, 9]


# ----------------------------------------------------
# 5. 字典推导式 (Dict Comprehension) 演示
# ----------------------------------------------------
# 目标: 创建一个键为数字，值为其平方的字典

dict_comprehension = {
    x: x*x for x in numbers[:5]
}

print("\n5. 字典推导式:")
print(f"   结果: {dict_comprehension}")
# 结果应该是: {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}