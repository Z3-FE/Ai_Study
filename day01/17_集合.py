
print('可变集合', "-" * 20)
# 可变集合 去重、无序
tests = {1, 2, 3, "test", True, False, None, 1}
print(type(tests),tests)

print('不可变集合', "-" * 20)
# 不可变集合
test2 = frozenset({1, 2, 3, "test", True, False, None, 1})
print(type(test2),test2)

print('转换为集合', "-" * 20)
# 可以转换 数组，元组，字符串，为不可变集合/可变集合
test3 = frozenset([1, 2, 3, "test", True, False, None, 1])
test4 = set([1, 2, 3, "test", True, False, None, 1])
print(type(test3), test3)
print(type(test4), test4)

# 【注】： 集合中不可以嵌套可变集合，可以嵌套不可变集合

print('增2种', "-" * 20)
# 增
test5 = {1,2}
# 单一增加
test5.add(3)
print(test5)
# 批量增加
test5.update([4, 5])
print(test5)

print('删除4种', "-" * 20)
#删除
test6 = {1, 2, 3,4,5}
# 移除指定元素。如果元素不存在，则会引发 KeyError 错误。
test6.remove(3)
print(test6)
# 移除指定元素。如果元素不存在，则不执行任何操作，也不会引发错误。
test6.discard(2)
print(test6)
# 随机移除并返回集合中的一个元素。由于集合是无序的，你无法确定哪个元素会被移除。
indexC = test6.pop()
print(indexC, test6)
# 清空集合中的所有元素。
test6.clear()
print(test6)

print('改一种', "-" * 20)
# 改
# 通过add remove实现
test7 = {1,2,3,4}
test7.remove(2)
test7.add(20)
print(test7)

print('查一种', "-" * 20)
# 查
# 通过成员运算符
test8 = {1,2,3,4}
result = 2 in test8
print(result)
result2 = 2 not in test8
print(result2)

print('集合常用方法', "-" * 20)

s1 = {10,20,30,40}
s2 = {30,40,50,60}
# 找出s1中不同于s2的数据 10，20
print('difference', '-'*20)
result3 = s1.difference(s2)
print(result3)

# 修改s1, 删除s1与s2相同的部分
print('difference_update','-' * 20)
s1.difference_update(s2)
print(s1)
print(s2)

# 合并
s3 = {1,2,3,4,5}
s4 = {1,2,3,4,5,6,7,8,9}
result4 = s3.union(s4)
print(result4)

print('issubset： 子集','-' * 20)
# 判断当前集合是否是 other 集合的子集（即当前集合的所有元素都包含在 other 中）
print({1, 2}.issubset({1, 2, 3}))

print('issuperset: 超集','-' * 20)
# 判断当前集合是否是 other 集合的超集（即 other 的所有元素都包含在当前集合中）。
print({1, 2, 3}.issuperset({1, 2}))

print('isdisjoint: 交集','-' * 20)
# 判断两个集合是否不相交（即它们没有共同的元素，交集为空）。
print({3}.isdisjoint({1, 2}))

