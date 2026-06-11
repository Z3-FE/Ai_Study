"""
 注意点
1、只能写一行，不能写多行代码。

2、不能写代码块（if、for、while）。

3、冒号右边必须是表达式，且只能写一个表达式。

4、表达式结果自动作为返回值。
"""
from functools import reduce


def calculate(func, a, b):
    return func(a,b)

# 匿名函数 lambda 参数: 函数体
print(calculate(lambda a, b: a * b, 1, 2))

students = [
    {'name': 'Alice', 'score': 92},
    {'name': 'Bob', 'score': 85},
    {'name': 'Charlie', 'score': 99}
]

# 使用 lambda 函数作为排序的 key / reverse true是升序， FALSE降序
sorted_students = sorted(students, key=lambda s: s['score'], reverse=True)

print("--- 按分数排序 ---")
for student in sorted_students:
    print(student)
# 排序结果将是: Bob (85), Alice (92), Charlie (99)


numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# 使用 lambda 函数作为过滤条件
even_numbers = list(filter(lambda n: n % 2 == 0, numbers))

print(f"\n--- 过滤偶数 ---")
print(even_numbers)  # 输出: [2, 4, 6, 8, 10]


numbers = [1, 2, 3, 4, 5]

# 使用 lambda 函数作为映射函数
squared_numbers = list(map(lambda n: n * n, numbers))

print(f"\n--- 映射平方 ---")
print(squared_numbers)  # 输出: [1, 4, 9, 16, 25]

print(f"\n--- 累计计算 ---")
print(reduce(lambda x, y: x + y, numbers))