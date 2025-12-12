def make_counter(initial_value):
    """
    外部函数：定义并初始化非局部变量 count。
    返回内部函数 increment。
    """
    # 非局部变量 (Enclosing scope)
    count = initial_value

    def increment(step=1):
        """
        内部函数 (闭包)：引用了外部函数的 count 变量。
        """
        # 使用 nonlocal 关键字声明要修改的是 E 作用域的 count
        nonlocal count
        count += step
        return count

    # 返回内部函数对象，而不是执行结果
    return increment


# ----------------------------------------------------
# 实例化闭包
# ----------------------------------------------------
# counter_a 成为一个闭包实例，它记住了 count=10 的状态
counter_a = make_counter(initial_value=10)
# counter_b 是另一个独立的闭包实例，它记住了 count=100 的状态
counter_b = make_counter(initial_value=100)

print("--- Counter A (初始值 10) ---")
print(f"A 第一次调用: {counter_a()}")  # count 变为 11
print(f"A 第二次调用: {counter_a(step=5)}")  # count 变为 16 (11 + 5)

print("\n--- Counter B (初始值 100) ---")
print(f"B 第一次调用: {counter_b()}")  # count 变为 101
print(f"B 第二次调用: {counter_b()}")  # count 变为 102

print("\n--- 验证闭包的独立性 ---")
# 验证 A 和 B 的状态是独立的
print(f"A 最终状态: {counter_a()}")  # 17
print(f"B 最终状态: {counter_b()}")  # 103
