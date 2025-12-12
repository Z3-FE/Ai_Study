# class SingletonDecorator:
#     """
#     类装饰器：用于将任何类转换为单例。
#     """
#
#     def __init__(self, decorated_class):
#         """1. __init__ 接收被装饰的类（User）。"""
#         self.decorated = decorated_class
#         self.instance = None
#
#     def __call__(self, *args, **kwargs):
#         """2. __call__ 使得装饰器实例可被调用，并控制实例化逻辑。"""
#         if self.instance is None:
#             # 如果实例不存在，则创建并保存实例
#             print(f"--- 单例创建: 首次创建 {self.decorated.__name__} 实例 ---")
#             self.instance = self.decorated(*args, **kwargs)
#         else:
#             print(f"--- 单例获取: 返回已存在的 {self.decorated.__name__} 实例 ---")
#
#         # 总是返回同一个实例
#         return self.instance
#
#
# @SingletonDecorator
# class DatabaseConnection:
#     def __init__(self, db_name):
#         self.db_name = db_name
#
#     def get_info(self):
#         return f"Database: {self.db_name}"
#
#
# # ----------------------------------------------------
# # 测试单例行为
# # ----------------------------------------------------
# conn1 = DatabaseConnection("ProdDB")  # 触发 SingletonDecorator.__call__，创建实例
# conn2 = DatabaseConnection("TestDB")  # 再次调用 __call__，返回已有的实例
#
# # 检查两个实例是否是同一个对象
# print(f"\n实例 1 ID: {id(conn1)}")
# print(f"实例 2 ID: {id(conn2)}")
#
# print(f"实例 1 的数据库名: {conn1.get_info()}")
# print(f"实例 2 的数据库名: {conn2.get_info()}")
# # 注意：虽然 conn2 传入了 "TestDB"，但它返回的是 conn1 的实例，因此数据库名仍是 "ProdDB"。

class Say:
    def __init__(self, message):
        print('__info__1111111111111')
        self.message = message

    def __call__(self, func):
        print(f'say_hello调用:{self.message}')

        def wrapper(*args, **kwargs):
            print('add调用')
            return func(*args, **kwargs)

        return wrapper


class Say2:
    def __init__(self, message):
        print('__info__22222222222')
        self.message = message

    def __call__(self, func):
        print(f'say_hello调用:{self.message}')

        def wrapper(*args, **kwargs):
            print('add调用')
            return func(*args, **kwargs)

        return wrapper


@Say2('Say222222222222222222')
@Say('Say')
def add(a, b):
    print('执行结果')
    return a + b


result = add(1, 2)
print(result)
