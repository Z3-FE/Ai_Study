"""
使用type()来判断数据类型
"""
import sys

res = type('字符串')
print(res)
res2 = type(123)
print(res2)

print(type(123.123))

#  当定义的数据很大时，可以中下划线进行数字分组，易读，不影响输出结果
age = 200_000
weight = 100_000_000

print(age, weight)
# python 中整数的上线值，取决于执行代码的计算机的内存和处理能力
a = 9 ** 9999
# 不能输出4300位以上的数据，调用
sys.set_int_max_str_digits(0)
print(a)