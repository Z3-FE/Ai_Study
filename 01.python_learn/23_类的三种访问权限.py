class AccessDemo:
    """
    演示 Python 中类的三种访问权限约定：
    1. 公有 (Public): 默认，无前缀
    2. 保护 (Protected): 单下划线前缀 (_)
    3. 私有 (Private): 双下划线前缀 (__)
    """

    def __init__(self, public_val, protected_val, private_val):
        # 1. 公有成员：可以在类内部和外部自由访问
        self.public_attribute = public_val

        # 2. 保护成员：约定上供类内部和子类使用，外部应避免直接访问
        self._protected_attribute = protected_val

        # 3. 私有成员：只能在当前类内部访问
        self.__private_attribute = private_val

    # ----------------------------------------------------
    # 类内部方法
    # ----------------------------------------------------

    def access_internal(self):
        """演示类内部对所有成员的访问"""
        print("\n--- 类内部访问 ---")
        print(f"公有属性 (public): {self.public_attribute}")
        print(f"保护属性 (_protected): {self._protected_attribute}")
        print(f"私有属性 (__private): {self.__private_attribute}")
        self.__internal_private_method() # 内部调用私有方法

    def __internal_private_method(self):
        """私有方法，只能在类内部调用"""
        print("  -> 私有方法被成功调用。")


# --- 实例化对象 ---
demo_obj = AccessDemo(
    public_val="我是公有数据",
    protected_val="我是保护数据",
    private_val="我是私有秘密"
)

# ----------------------------------------------------
# 类外部访问测试
# ----------------------------------------------------
print("\n" + "="*40)
print("             外部访问测试")
print("="*40)

# 1. 公有访问 (推荐且自由)
print("1. 公有访问 (Public):")
print(f"   读取: {demo_obj.public_attribute}")
demo_obj.public_attribute = "公有数据已修改"
print(f"   修改后读取: {demo_obj.public_attribute}")

print("\n2. 保护访问 (Protected):")
# 2. 保护访问 (技术上可行，但约定上不推荐)
print(f"   读取: {demo_obj._protected_attribute}")
demo_obj._protected_attribute = "保护数据已修改"
print(f"   修改后读取: {demo_obj._protected_attribute}")


print("\n3. 私有访问 (Private):")
# 3. 私有访问 (正常情况下会失败，达到封装目的)
try:
    print(demo_obj.__private_attribute)
except AttributeError as e:
    print(f"   ❌ 失败! 外部无法直接访问私有属性。")
    print(f"   错误信息: {e}")


# 4. 演示私有机制：名称修饰 (Name Mangling)
print("\n4. 私有机制：名称修饰 (Name Mangling):")
# Python 编译器将 __private_attribute 自动重命名为 _AccessDemo__private_attribute
mangled_name = '_AccessDemo__private_attribute'
print(f"   私有属性的真实名称: {mangled_name}")

# 通过绕过机制访问 (不推荐用于生产环境)
print(f"   ⚠️ 绕过机制访问: {getattr(demo_obj, mangled_name)}")


# 5. 调用类内部方法
demo_obj.access_internal()