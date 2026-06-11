from typing import List, Dict, Tuple, Optional, Union, Set

# 也可以使用 Python 3.10+ 的原生联合类型操作符 | 代替 Union 和 Optional

# ----------------------------------------------------
# 1. 基础类型注解
# ----------------------------------------------------

# 变量注解
MAX_USERS: int = 500
API_KEY: str = "abc-123-xyz"
IS_DEBUG_MODE: bool = False


# 基础函数注解
def add(a: int, b: int) -> int:
    """计算两个整数的和，返回整数。"""
    return a + b


def display_info(message: str) -> None:
    """打印信息，函数没有返回值 (返回 None)。"""
    print(f"[INFO] {message}")


# ----------------------------------------------------
# 2. 复杂集合类型注解 (使用 typing 模块)
# ----------------------------------------------------

# 函数接收一个元素为字符串的列表，返回一个集合
def process_tags(tag_list: List[str]) -> Set[str]:
    """将标签列表转换为集合，去除重复项。"""
    print(f"原始标签数: {len(tag_list)}")
    return set(tag_list)


# 函数接收一个字典，返回一个浮点数
def calculate_average_price(item_prices: Dict[str, float]) -> float:
    """计算字典中所有价格的平均值。"""
    if not item_prices:
        return 0.0
    total = sum(item_prices.values())
    return total / len(item_prices)


calculate_average_price({'a': 1.2, 'b': 2.3, 'c': 3.4})


# 函数接收和返回一个固定结构的元组
def get_user_status(user_id: int) -> Tuple[str, bool, int]:
    """返回 (用户名, 是否在线, 最后登录时间戳)。"""
    # 模拟数据查询
    return ("user_alice", True, 1678886400)


source: Tuple[int | str, ...] = (1, 4, '2', 3)


# ----------------------------------------------------
# 3. 可选和联合类型注解
# ----------------------------------------------------

# Optional (类型或 None) / Python 3.10+ 可使用 T | None
def find_config(key: str) -> Optional[str]:
    """查找配置项。如果找不到，返回 None。"""
    config_data = {"API_URL": "http://api.example.com"}
    return config_data.get(key)


# Union (多种类型之一) / Python 3.10+ 可使用 int | float
def scale_value(value: Union[int, float], factor: float) -> Union[int, float]:
    """将数值放大。输入什么类型，就返回什么类型（简化演示）。"""
    return value * factor


# ----------------------------------------------------
# 4. 类和类型别名注解
# ----------------------------------------------------

# 自定义类型别名 (提高可读性)
UserID = int
ResponseCode = int
UserMap = Dict[UserID, str]  # {1: 'Alice', 2: 'Bob'}


class User:
    def __init__(self, user_id: UserID, name: str):
        self.user_id = user_id
        self.name = name


def lookup_user(user_map: UserMap, user_id: UserID) -> Optional[User]:
    """根据 ID 查找用户对象。"""
    if user_id in user_map:
        return User(user_id, user_map[user_id])
    return None


# ----------------------------------------------------
# 示例运行
# ----------------------------------------------------

print(f"Sum (10 + 5): {add(10, 5)}")

# 示例 2: 复杂集合
my_tags = ["python", "code", "python", "test"]
unique_tags = process_tags(my_tags)
print(f"处理后的唯一标签: {unique_tags}")

# 示例 3: 可选类型
api_key_found = find_config("API_URL")
api_key_missing = find_config("INVALID_KEY")
print(f"API Key Found: {api_key_found}")
print(f"API Key Missing: {api_key_missing}")

# 示例 4: 类和类型别名
user_data: UserMap = {1: "Alice", 2: "Bob"}
user_obj = lookup_user(user_data, 1)

if user_obj:
    print(f"查找结果: User ID {user_obj.user_id}, Name: {user_obj.name}")
