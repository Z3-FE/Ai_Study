import copy

# ----------------------------------------------------
# 原始数据结构
# ----------------------------------------------------
# 包含一个可变对象（子列表）的列表
original_list = [100, [1, 2, 3], 200]
print(f"原始列表 (ID):       {id(original_list)}")
print(f"原始子列表 (ID):     {id(original_list[1])}")
print(f"原始数据:          {original_list}")


# ----------------------------------------------------
# 1. 直接赋值 (Direct Assignment)
# ----------------------------------------------------
print("\n" + "=" * 50)
print("1. 直接赋值 (a = b) - 共享对象")
print("=" * 50)

assignment_copy = original_list
print(f"赋值拷贝 (ID):       {id(assignment_copy)}")
# ID 相同： assignment_copy 和 original_list 指向内存中的同一个对象

# 修改赋值拷贝的元素
assignment_copy.append(300)

print(f"赋值后 Original:   {original_list}") # 原始列表也被修改了
print(f"赋值后 Assignment: {assignment_copy}") # 结果一致


# ----------------------------------------------------
# 2. 浅拷贝 (Shallow Copy)
# ----------------------------------------------------
print("\n" + "=" * 50)
print("2. 浅拷贝 (Shallow Copy) - 共享子对象")
print("=" * 50)

# 使用 copy.copy() 或切片 [:]
shallow_copy = copy.copy(original_list)

print(f"浅拷贝 (新容器ID):   {id(shallow_copy)}")
print(f"浅拷贝子列表 (ID):   {id(shallow_copy[1])}")
# 浅拷贝：顶层ID不同，子对象ID相同

# --- 2a. 顶层修改测试 (不会互相影响) ---
shallow_copy.append(400)
print("\n--- 2a. 顶层修改测试 ---")
print(f"Original: {original_list}")    # 未受影响
print(f"Shallow:  {shallow_copy}")     # 已添加 400

# --- 2b. 子对象修改测试 (会互相影响) ---
# 修改子列表 [1, 2, 3]
shallow_copy[1].append(99)
print("\n--- 2b. 子对象修改测试 ---")
print(f"Original: {original_list}")    # 原始列表的子列表被修改了!
print(f"Shallow:  {shallow_copy}")     # 子列表被修改了


# ----------------------------------------------------
# 3. 深拷贝 (Deep Copy)
# ----------------------------------------------------
# 恢复原始状态（防止浅拷贝的影响持续）
original_list = [100, [1, 2, 3], 200]

print("\n" + "=" * 50)
print("3. 深拷贝 (Deep Copy) - 完全独立")
print("=" * 50)

deep_copy = copy.deepcopy(original_list)

print(f"深拷贝 (新容器ID):   {id(deep_copy)}")
print(f"深拷贝子列表 (ID):   {id(deep_copy[1])}")
# 深拷贝：顶层ID不同，子对象ID也不同（完全独立）

# --- 3. 子对象修改测试 (不会互相影响) ---
# 修改深拷贝的子列表
deep_copy[1].append(888)

print("\n--- 3. 子对象修改测试 ---")
print(f"Original: {original_list}")    # 未受影响!
print(f"Deep:     {deep_copy}")       # 独立修改


# ----------------------------------------------------
# 结论
# ----------------------------------------------------
print("\n" + "=" * 50)
print("结论：")
print("  - 赋值: 共享对象 (改一个，全变)。")
print("  - 浅拷贝: 共享子对象 (只改顶层安全，改子对象互相影响)。")
print("  - 深拷贝: 完全独立 (任何修改都不影响原对象)。")