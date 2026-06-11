def log_execution(func):
    """
    装饰器函数：接受原函数作为参数。
    """

    # 闭包/包装函数：捕获了 func，并接受任意参数
    def wrapper(*args, **kwargs):
        # 1. 前置操作 (增强功能)
        print(f"--- LOG: 正在执行函数: {func.__name__} ---")

        # 2. 调用原函数
        result = func(*args, **kwargs)

        # 3. 后置操作 (增强功能)
        print(f"--- LOG: 函数 {func.__name__} 执行完毕。---")

        # 4. 返回原函数的返回值
        return result

    # 返回增强后的 wrapper 函数
    return wrapper


# ----------------------------------------------------
# 使用装饰器
# ----------------------------------------------------

@log_execution
def calculate_sum(a, b):
    print(f"   原函数内部: 计算 {a} + {b}")
    return a + b


@log_execution
def greet(name):
    print(f"   原函数内部: 问候 {name}")
    return f"Hello, {name}!"


# 调用被装饰的函数
sum_result = calculate_sum(10, 20)
print(f"返回值: {sum_result}\n")

greeting = greet("Alice")
print(f"返回值: {greeting}")
