from functools import wraps


# 调用栈的逻辑是 从最外层开始执行包装函数，但最内层的装饰器先被应用（先返回）。
def outer_decorator(func):
    """最外层装饰器 (先执行 wrapper 逻辑)"""
    print('AAAAA')

    @wraps(func)
    def wrapper(*args, **kwargs):
        print(">>>>> [A] 外层装饰器逻辑开始 <<<<<")
        result = func(*args, **kwargs)
        print(">>>>> [A] 外层装饰器逻辑结束 <<<<<")
        return result

    return wrapper


def inner_decorator(func):
    """内层装饰器 (后执行 wrapper 逻辑)"""
    print('BBBBB')

    @wraps(func)
    def wrapper(*args, **kwargs):
        print("    --- [B] 内层装饰器逻辑开始 ---")
        result = func(*args, **kwargs)
        print("    --- [B] 内层装饰器逻辑结束 ---")
        return result

    return wrapper


# ----------------------------------------------------
# 应用多个装饰器
# ----------------------------------------------------

@outer_decorator  # 装饰器 A (外层)
@inner_decorator  # 装饰器 B (内层)
def say_hello(name):
    print(f"        原函数内部: Hello, {name}!")


# ----------------------------------------------------
# 调用函数  outer_decorator（inner_decorator（say_hello（）））
# ----------------------------------------------------
print("--- 调用栈执行顺序 ---")
say_hello("World")
