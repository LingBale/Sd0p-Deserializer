_strategies = {}

# V3-0: 高级策略注册表
_advanced_strategies = {}

def register_strategy(tag: str):
    def decorator(cls):
        _strategies[tag] = cls() # 实例化策略
        return cls
    return decorator

def get_strategy(tag: str):
    return _strategies.get(tag)

# V3-0: 高级策略注册与获取函数
def register_advanced_strategy(condition_func):
    """
    注册高级策略
    
    :param condition_func: 条件函数，接收 features 参数，返回 bool
    :return: 装饰器
    """
    def decorator(cls):
        _advanced_strategies[condition_func] = cls()
        return cls
    return decorator

def get_advanced_strategy(features):
    """
    获取匹配的高级策略
    
    遍历所有注册的条件函数，找到第一个匹配的策略并返回。
    
    :param features: 特征对象
    :return: 匹配的策略实例，如果没有匹配则返回 None
    """
    for condition_func, strategy in _advanced_strategies.items():
        if condition_func(features):
            return strategy
    return None
