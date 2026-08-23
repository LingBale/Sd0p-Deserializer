from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class MethodInfo:
    name: str
    body: str = ""
    params: List[str] = field(default_factory=list)
    is_static: bool = False

@dataclass
class PropertyInfo:
    name: str
    visibility: str = "public"  # public, protected, private
    default_value: Any = None
    is_static: bool = False

@dataclass
class ClassInfo:
    """统一的类信息模型"""
    name: str
    short_name: str
    namespace: Optional[str] = None
    parent_class: Optional[str] = None
    
    properties: Dict[str, PropertyInfo] = field(default_factory=dict)
    methods: Dict[str, MethodInfo] = field(default_factory=dict)
    
    # 继承合并后的结果
    all_properties: Dict[str, PropertyInfo] = field(default_factory=dict)
    all_methods: Dict[str, MethodInfo] = field(default_factory=dict)
    
    has_serialize_hook: bool = False  # P2-1: PHP 7.4+ __serialize support
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeatureSet:
    """统一的特征集模型"""
    has_wakeup: bool = False
    has_destruct: bool = False
    has_tostring: bool = False
    dangerous_calls: List[Dict[str, str]] = field(default_factory=list)
    destruct_conditions: List[Dict[str, Any]] = field(default_factory=list)
    md5_weak_conditions: List[Dict[str, str]] = field(default_factory=list)
    builtin_class_conditions: List[Dict[str, str]] = field(default_factory=list)
    pop_chain_conditions: List[Dict[str, str]] = field(default_factory=list)
    callback_rce_conditions: List[Dict[str, str]] = field(default_factory=list)
    string_escape_conditions: List[Dict[str, Any]] = field(default_factory=list)
    new_expressions: List[Dict[str, str]] = field(default_factory=list)
    dynamic_prop_assign: List[Dict[str, str]] = field(default_factory=list) # 动态属性赋值
    reference_map: Dict[str, str] = field(default_factory=dict) # P2-2: 引用关系 { 'A': 'B' } means A references B
    tags: List[str] = field(default_factory=list)
    source_file: str = "" # 记录类所在的源文件路径
