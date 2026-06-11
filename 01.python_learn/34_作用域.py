# B: Built-in 作用域的变量，如 print, len, str 等
# G: Global 作用域的变量 (模块级别)
global_var = "我是全局变量 (G)"


def outer_function(outer_param):  # outer_param 属于 E 作用域
    # G 作用域内的代码块

    # E: Enclosing 作用域的变量
    enclosing_var = "我是嵌套变量 (E)"

    def inner_function(local_param):  # local_param 属于 L 作用域
        # E 作用域内的代码块

        # L: Local 作用域的变量
        local_var = "我是局部变量 (L)"

        print("\n--- 在 L 作用域内部查找变量 ---")

        # 1. 查找 L (Local)
        print(f"L 作用域: {local_var}")

        # 2. 查找 E (Enclosing)
        print(f"E 作用域: {enclosing_var}")

        # 3. 查找 G (Global)
        print(f"G 作用域: {global_var}")

        # 4. 查找 B (Built-in)
        print(f"B 作用域 (内置函数): {len('test')}")

    inner_function("L_param_value")


# 执行外部函数
outer_function("E_param_value")

# ----------------------------------------
# 在 G 作用域 (模块顶层) 尝试查找
# ----------------------------------------
print("\n--- 在 G 作用域内部查找变量 ---")
print(f"G 作用域: {global_var}")

# 尝试在 G 作用域访问 L 或 E 变量 (会失败)
try:
    print(local_var)
except NameError as e:
    print(f"❌ 错误: 无法在 G 作用域中访问局部变量: {e}")

count = 0


def increment_global():
    global count  # 声明要修改的是 G 作用域的 count
    count += 1


def outer():
    message = "Hi"

    def inner():
        nonlocal message  # 声明要修改的是 E 作用域的 message
        message = "Hello"

    inner()
    print(message)  # 输出: Hello
