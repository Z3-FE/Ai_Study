# 初始列表
fruits = ["apple", "banana", "cherry"]
print(f"原始列表: {fruits}")
print("-" * 20)

### ➕ 增 (Add / Insert) 操作 ###

# 1. append()：在末尾添加一个元素
fruits.append("date")
print(f"使用 append() 添加 'date': {fruits}")

# 2. insert()：在索引 1 处插入一个元素
fruits.insert(1, "grape")
print(f"使用 insert() 插入 'grape': {fruits}")

# 3. extend()：添加另一个列表中的多个元素
more_fruits = ["kiwi", "mango"]
fruits.extend(more_fruits)
print(f"使用 extend() 添加列表: {fruits}")

print("-" * 20)

### 🔎 查 (Retrieve / Query) 操作 ###

# 1. 索引访问：获取第一个元素 (索引 0)
first_fruit = fruits[0]
print(f"第一个元素 (索引 0): {first_fruit}")

# 2. 切片访问：获取从索引 2 到索引 4 (不包含 5) 的元素
slice_fruits = fruits[2:5]
slice_fruits2 = fruits[2:5:2]
print(f"切片 [2:5] 结果: {slice_fruits}")
print(f"切片 [2:5] 结果,间隔取出: {slice_fruits2}")

# 3. index()：查找 'date' 元素的索引
try:
    date_index = fruits.index("date")
    print(f"'date' 的索引位置: {date_index}")
except ValueError:
    print("'date' 未找到。")

# 4. in 关键字：检查 'kiwi' 是否存在
is_kiwi_present = "kiwi" in fruits
print(f"列表包含 'kiwi' 吗? {is_kiwi_present}")

print("-" * 20)

### ➖ 删 (Delete / Remove) 操作 ###

# 1. pop()：移除并返回最后一个元素
last_fruit = fruits.pop()
print(f"使用 pop() 移除并返回: {last_fruit}")
print(f"列表剩余元素: {fruits}")

# 2. pop(index)：移除索引 0 处的元素
first_removed = fruits.pop(0)
print(f"使用 pop(0) 移除并返回: {first_removed}")
print(f"列表剩余元素: {fruits}")

# 3. remove(value)：移除列表中找到的第一个 'cherry'
try:
    fruits.remove("cherry")
    print(f"使用 remove('cherry') 后的列表: {fruits}")
except ValueError:
    print("'cherry' 未找到，无法移除。")

# 4. del 语句：删除指定范围 (索引 2) 的元素
# 假设当前列表为 ['grape', 'banana', 'date', 'kiwi']
del fruits[2]
print(f"使用 del fruits[2] 后的列表: {fruits}")

# 5. clear()：清空整个列表
# fruits.clear()
# print(f"使用 clear() 后的列表: {fruits}")

# 常用方法
print('数组长度:', len(fruits))

print("-" * 20)

# 数组转换字符串
print('数组转换字符串', '-'.join(['a', 'b', 'c']))