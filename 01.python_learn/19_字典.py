# 初始化一个示例字典 JSON
person = {
    "name": "Alice",
    "age": 25,
    "city": "London"
}

print("--- 原始字典 ---")
print(f"原始字典: {person}")
print("-" * 30)

# --- 1. 增加/修改 (Add/Update) ---
print("--- 1. 增加/修改 ---")

# 1.1 修改现有键的值 (修改)
person['age'] = 26
print(f"修改 age 后: {person}")

# 1.2 添加新的键值对 (增加)
person['occupation'] = 'Engineer'
print(f"增加 occupation 后: {person}")

# 1.3 使用 .update() 合并另一个字典 (增/改)
person.update({'city': 'New York', 'email': 'alice@example.com'})
print(f"使用 update() 后: {person}")

# 1.4 使用数学运算
print('数学运算',person | {"name": "Jane", "job": "Developer"})

# 1.4 使用 .setdefault() 尝试添加不存在的键
score = person.setdefault('score', 95)
print(f"使用 setdefault() 添加 score: {person}")
print(f"获取的 score 值为: {score}")

# 1.5 使用 .setdefault() 获取已存在的键 (不会修改值)
age = person.setdefault('age', 999) # 键已存在，不会修改为 999
print(f"使用 setdefault() 获取 age: {person}")
print(f"获取的 age 值为: {age}")
print("-" * 30)


# --- 2. 查询 (Get) ---
print("--- 2. 查询 ---")

# 2.1 使用方括号 [] 获取值 (键不存在会报错)
try:
    name = person['name']
    print(f"使用 [] 获取 name: {name}")
    # person['non_existent_key'] # 运行这行会引发 KeyError
except KeyError as e:
    print(f"使用 [] 访问不存在的键会引发错误: {e}")

# 2.2 使用 .get() 获取值 (键不存在返回默认值)
job = person.get('occupation')
print(f"使用 .get() 获取 occupation: {job}")

missing_key = person.get('address', '地址未知')
print(f"使用 .get() 获取不存在的键: {missing_key}")
print("-" * 30)


# --- 3. 视图方法 (Views) ---
print("--- 3. 视图方法 ---")

# 3.1 获取所有键
keys_view = person.keys()
print(f"所有键 (.keys()): {keys_view}")

# 3.2 获取所有值
values_view = person.values()
print(f"所有值 (.values()): {values_view}")

# 3.3 获取所有项 (键值对)
items_view = person.items()
print(f"所有项 (.items()): {items_view}")

# 视图是动态的，原字典改变，视图也会改变
person['gender'] = 'F'
print(f"添加 gender 后 items 视图自动更新: {person.items()}")
print("-" * 30)


# --- 4. 删除 (Delete) ---
print("--- 4. 删除 ---")

# 4.1 使用 del 关键字删除
del person['email']
print(f"使用 del 删除 email 后: {person}")

# 4.2 使用 .pop() 删除并返回值
removed_city = person.pop('city')
print(f"使用 .pop() 删除并返回 city ({removed_city}) 后: {person}")

# 4.3 使用 .popitem() 删除最后一项
last_item = person.popitem()
print(f"使用 .popitem() 删除最后一项 ({last_item}) 后: {person}")

# 4.4 清空字典
person.clear()
print(f"使用 .clear() 清空字典后: {person}")

# 尝试对空字典使用 popitem 会报错
try:
    person.popitem()
except KeyError as e:
    print(f"对空字典使用 .popitem() 会引发错误: {e}")