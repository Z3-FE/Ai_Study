# 定义处：这是“打包/收集” (Packing)
# 职责：准备好接收任何形式的包裹
def func(*args, **kwargs):
    print(args)
    print(kwargs)


params = {"name": "Bob", "age": 20}

# 调用处：这是“解包” (Unpacking)
# 职责：把现有的字典拆开塞进函数
func("tool1", "tool2", "tool3", **params)
