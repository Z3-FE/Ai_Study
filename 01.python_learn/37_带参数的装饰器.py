from functools import wraps


def log_decorator(level):
    """
    1. 最外层函数 (参数工厂)：接收装饰器的配置参数 (level)。
    """

    # 2. 真正的装饰器函数：接收被装饰的原函数 (func)。
    def decorator(func):

        # 使用 @wraps 保持原函数的元数据
        @wraps(func)
        # 3. 闭包/包装函数：接收原函数的参数 (*args, **kwargs)。
        def wrapper(*args, **kwargs):

            # 增强逻辑：利用了外层捕获的配置参数 'level'
            if level == 'CRITICAL':
                print(f"[{level}] 严重警告! 函数 {func.__name__} 即将被调用...")
            else:
                print(f"[{level}] 正在执行函数: {func.__name__}")

            # 调用原函数
            result = func(*args, **kwargs)

            print(f"[{level}] 函数 {func.__name__} 执行完毕。")

            return result

        # 第二层返回第三层
        return wrapper

    # 第一层返回第二层
    return decorator


# ----------------------------------------------------
# 使用带参数的装饰器
# ----------------------------------------------------

# 示例 1: 传入参数 'CRITICAL'，触发特殊逻辑
@log_decorator(level='CRITICAL')
def process_data(data):
    """处理关键数据"""
    print(f"   原函数内部: 正在处理 {len(data)} 条数据")
    return len(data)


# 示例 2: 传入参数 'INFO'，触发普通逻辑
@log_decorator(level='INFO')
def calculate_metrics(a, b):
    """计算指标"""
    print(f"   原函数内部: 计算 {a} + {b}")
    return a + b


# ----------------------------------------------------
# 调用被装饰的函数
# ----------------------------------------------------
print("--- 调用 process_data (CRITICAL 级别) ---")
process_data([1, 2, 3])

print("\n--- 调用 calculate_metrics (INFO 级别) ---")
calculate_metrics(10, 5)
