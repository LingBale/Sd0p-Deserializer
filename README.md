# Sd0p-V3.5

面向 PHP 反序列化漏洞的 CTF 自动化 Payload 生成工具。提供 PyQt6 图形界面，集成 PHP 代码解析、POP 链推导、字符串逃逸构造、内置类利用、PHAR 反序列化、HTTP 投递与 POP 链可视化等能力。

## 主要功能

| 模块 | 能力 |
|---|---|
| POP 链分析 | 递归推导 `__destruct` / `__wakeup` / `__toString` / `__call` 等魔术方法链路 |
| Payload 生成 | 标准策略 + 高级策略（Fiber、SplFixedArray、PHP-FPM、PHP 8.1 Enum 等） |
| 字符串逃逸 | 自动识别 `str_replace` / `preg_replace` 长度变换场景，构造逃逸 Payload |
| 内置类利用 | SimpleXMLElement XXE、SoapClient SSRF、SplFileObject LFI、Error/Exception XSS |
| PHAR 反序列化 | 文件上传触发 phar 协议反序列化链 |
| 多文件分析 | 拼接多个 PHP 文件联合分析跨类 POP 链 |
| HTTP 投递 | 内置 HTTP 客户端，支持自定义请求模板与预览 |
| POP 链可视化 | 基于 networkx + matplotlib 渲染调用图 |
| AI 建议 | 针对复杂场景给出构造思路提示 |

## 技术栈

- **语言**: Python 3.8+
- **GUI**: PyQt6
- **图形渲染**: matplotlib + networkx
- **HTTP**: requests
- **打包**: PyInstaller（`--onefile` 单文件分发）

## 项目结构

```
Sd0p-v3.0/
├── core_v2/                 # 核心引擎
│   ├── engine.py            # Sd0pEngineV2 主入口（编排解析→特征→POP→策略→Payload）
│   ├── parser/              # PHP 源码解析器
│   ├── detector/            # 特征提取（魔术方法、sink、字符串逃逸）
│   ├── chain/               # POP 链递归解析与调用图构建
│   ├── strategy/            # Payload 生成策略（standard + advanced）
│   ├── composer/            # Payload 组合器
│   ├── serializer/          # PHP 序列化字符串构造
│   ├── phar/                # PHAR 反序列化支持
│   ├── http/                # 内置 HTTP 客户端
│   ├── sandbox/             # 沙箱执行
│   ├── ai/                  # AI 建议模块
│   ├── model/               # ClassInfo / FeatureSet 数据模型
│   └── utils/               # 工具（escape_detector、session_converter 等）
├── ui_v2/                   # PyQt6 GUI
│   ├── main_window.py       # V2MainWindow 主窗口（标签页注册）
│   ├── views/               # Dashboard / PopChain / Exploit / MultiFile / Phar / AdvancedTools
│   ├── controllers/         # 控制器层
│   ├── components/          # 可复用组件
│   └── widgets/             # 自定义控件（HTTP 预览对话框等）
├── docker/                  # PHP 7.4 / 8.1 测试环境与 payload 运行器
├── docs/                    # 项目文档（V2_UI_GUIDE.md 等）
├── tests/                   # 核心单元测试（test_v2_e2e.py、test_string_escape.py）
├── run_ui_v2.py             # GUI 启动入口
├── Sd0p-V3.5.spec           # PyInstaller 打包配置
├── ManS2.ico                 # 程序图标
├── requirements.txt         # Python 依赖清单
├── BUILD_INSTRUCTIONS.md    # 打包与分发说明
└── RELEASE_NOTES.md         # 历史发行说明
```

## 快速开始

### 方式一：运行可执行文件（最终用户）

下载 `Sd0p-V3.5.exe`，双击即可运行，无需安装 Python 或任何依赖。

### 方式二：从源码运行（开发者）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 GUI
python run_ui_v2.py
```

### 方式三：从源码构建可执行文件

参见 [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)。核心命令：

```bash
pyinstaller --onefile --windowed --name="Sd0p-V3.5" \
  --icon="ManS2.ico" \
  --add-data="core_v2;core_v2" \
  --add-data="ui_v2;ui_v2" \
  --hidden-import="matplotlib" \
  --hidden-import="networkx" \
  run_ui_v2.py
```

构建产物位于 `dist/Sd0p-V3.5.exe`。

## 引擎工作流程

`Sd0pEngineV2.analyze_and_generate(php_code)` 主流程：

1. **解析** — `PhpParserV2` 提取类、属性、方法、魔术方法
2. **无类场景** — 进入 `_generate_native_class_payload`：识别字符串逃逸 / echo 触发 / 文件读取等场景，生成对应内置类 Payload
3. **特征提取** — `FeatureExtractorV2` 输出 `FeatureSet`（has_wakeup、has_destruct、pop_chain_conditions 等）
4. **POP 链解析** — `PopChainResolver` 递归合并跨类属性
5. **策略路由** — 先匹配高级策略（advanced），未命中则走 standard 策略
6. **Payload 生成** — 通过 `serialize_php` 构造合法 PHP 序列化字符串

## 测试

```bash
# 核心单元测试
python -m pytest tests/ -v
```

`tests/` 目录包含端到端引擎测试与字符串逃逸场景测试。`docker/` 目录提供 PHP 7.4 / 8.1 容器用于 Payload 实际执行验证。

## 文档

- [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) — 打包与分发指南
- [RELEASE_NOTES.md](RELEASE_NOTES.md) — 历史发行说明
- [docs/V2_UI_GUIDE.md](docs/V2_UI_GUIDE.md) — V2 UI 使用与架构说明

## 注意事项

- 本项目为安全研究工具，请仅用于合法的 CTF 竞赛或授权的安全测试。
- 部分高级策略依赖特定 PHP 版本（如 Fiber 需 PHP 8.1+、SplFixedArray 整数溢出需 PHP 7.0–7.4）。
- 未签名可执行文件可能被杀毒软件误报，请加入信任区。
