# 元组只能查 tuple
t1 = (1, 2, 3)
t2 = ('a', 'b', 'c')

print(type(t1))
print(t1[1])
print(t2[1])

# 常用方法
my_tuple = ('a', 'b', 'c', 'd', 'b')

# 查找 'c' 的索引
index_c = my_tuple.index('c')
print(f"'c' 第一次出现的索引: {index_c}")
# 输出: 'c' 第一次出现的索引: 2

# 查找 'b' 的索引 (只会返回第一次出现的索引)
index_b = my_tuple.index('b')
print(f"'b' 第一次出现的索引: {index_b}")
# 输出: 'b' 第一次出现的索引: 1

# 查找不存在的元素会报错
try:
    my_tuple.index('z')
except ValueError as e:
    print(f"查找 'z' 报错: {e}")
    # 输出: 查找 'z' 报错: tuple.index(x): x not in tuple
my_tuple = (10, 20, 10, 30, 10, 40)


# 查找 10 出现的次数
count_of_ten = my_tuple.count(10)
print(f"元组中 10 出现的次数: {count_of_ten}")
# 输出: 元组中 10 出现的次数: 3

# 查找 50 出现的次数
count_of_fifty = my_tuple.count(50)
print(f"元组中 50 出现的次数: {count_of_fifty}")
# 输出: 元组中 50 出现的次数: 0