class NamedObject:
    # 接受 **kwargs 并传递给 super()
    def __init__(self, name, **kwargs):
        # 提取自己需要的参数 name
        self.name = name
        print(f"NamedObject init for: {self.name}")

        # 将剩余的参数传递给 MRO 链中的下一个类
        super().__init__(**kwargs)


class LoggedObject:
    # 接受 **kwargs 并传递给 super()
    def __init__(self, log_level, **kwargs):
        # 提取自己需要的参数 log_level
        self.log_level = log_level
        print(f"LoggedObject init with level: {self.log_level}")

        # 将剩余的参数传递给 MRO 链中的下一个类
        super().__init__(**kwargs)  # 最终会调用 object.__init__()


class MyFeature(NamedObject, LoggedObject):
    def __init__(self, name, log_level, feature_id):
        # 方法一 推荐
        # MyFeature 接收所有参数，并一次性全部传递给 super()
        # MRO 会依次传递这些参数，直到每个类取走自己所需的参数
        super().__init__(name=name, log_level=log_level)

        # 方法二 ： 不推荐
        # # 显式调用 ParentA 的 __init__
        # NamedObject.__init__(self, name)
        # # 显式调用 ParentB 的 __init__
        # LoggedObject.__init__(self, log_level)

        self.feature_id = feature_id
        print(f"MyFeature init with ID: {self.feature_id}")


# 实例化 (现在可以成功运行)
feature = MyFeature(name="Task1", log_level="DEBUG", feature_id=101)

print("\n--- MRO 顺序 ---")
print(MyFeature.mro())
