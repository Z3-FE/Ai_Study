# 初始化两个示例集合
set_A = {1, 2, 3, 4, 5}
set_B = {4, 5, 6, 7, 8}

print("--- 原始集合 ---")
print(f"集合 A: {set_A}")
print(f"集合 B: {set_B}")
print("-" * 20)


## 1. 并集 (Union) - 包含 A 或 B 中的所有元素
# 数学符号: A U B

# 方法实现: .union()
union_by_method = set_A.union(set_B)
# 操作符实现: |
union_by_operator = set_A | set_B

print("1. 并集 (Union): A ∪ B")
print(f"   结果: {union_by_operator}") # 预期: {1, 2, 3, 4, 5, 6, 7, 8}
print("-" * 20)


## 2. 交集 (Intersection) - 包含 A 和 B 共同的元素
# 数学符号: A ∩ B

# 方法实现: .intersection()
intersection_by_method = set_A.intersection(set_B)
# 操作符实现: &
intersection_by_operator = set_A & set_B

print("2. 交集 (Intersection): A ∩ B")
print(f"   结果: {intersection_by_operator}") # 预期: {4, 5}
print("-" * 20)


## 3. 差集 (Difference) - 包含 A 中有但 B 中没有的元素 (顺序重要)
# 数学符号: A - B

# 方法实现: .difference()
difference_by_method = set_A.difference(set_B)
# 操作符实现: -
difference_by_operator = set_A - set_B

print("3. 差集 (Difference): A - B")
print(f"   A - B 结果: {difference_by_operator}") # 预期: {1, 2, 3}

# 反向差集 B - A
print(f"   B - A 结果: {set_B - set_A}") # 预期: {6, 7, 8}
print("-" * 20)


## 4. 对称差集 (Symmetric Difference) - 包含只属于 A 或只属于 B 的元素
# 数学符号: A Δ B

# 方法实现: .symmetric_difference()
sym_diff_by_method = set_A.symmetric_difference(set_B)
# 操作符实现: ^
sym_diff_by_operator = set_A ^ set_B

print("4. 对称差集 (Symmetric Difference): A Δ B")
print(f"   结果: {sym_diff_by_operator}") # 预期: {1, 2, 3, 6, 7, 8}
print("-" * 20)


## 5. 原地修改操作 (In-Place Operations)
# 注意: 原地修改会改变原集合的内容，因此我们使用一个新的可变集合 C 来演示
C = {10, 20, 30}
D = {20, 40, 50}
print(f"演示原地修改：C={C}, D={D}")

# 原地交集 (C 只保留与 D 的共同部分)
C &= D
print(f"C &= D 后的 C: {C}") # 预期: {20}