# NoxRunner 架构说明

## 架构层次

```
┌─────────────────────────────────────┐
│   NoxRunnerClient (对外 API)        │
│   - 统一接口                         │
│   - 自动选择后端                     │
│   - 提供便捷方法                     │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                 │
┌──────▼──────┐  ┌──────▼──────────┐
│ LocalBackend│  │ HTTPSandboxBackend│
│ (实现)      │  │ (实现)            │
└──────┬──────┘  └──────┬───────────┘
       │                 │
       └────────┬────────┘
                │
    ┌───────────┴────────────┐
    │                         │
┌───▼──────────┐    ┌────────▼────────┐
│ Security      │    │ FileOps         │
│ (内部模块)    │    │ (内部模块)      │
│               │    │                 │
│ - CommandVal  │    │ - TarHandler    │
│ - PathSanit   │    │                 │
└───────────────┘    └─────────────────┘
```

## 模块职责

### 1. Client 层 (对外 API)

**NoxRunnerClient** - 对外暴露的统一接口

- 自动选择后端（local 或 http）
- 提供便捷方法（如 `download_workspace`）
- 用户直接使用的 API

**职责**:
- 后端选择和管理
- 提供高级便捷方法
- 错误处理和转换

### 2. Backend 层 (实现层)

**LocalBackend** - 本地文件系统后端实现
- 实现 `SandboxBackend` 接口
- 使用 `security` 和 `fileops` 模块
- 在本地文件系统执行命令

**HTTPSandboxBackend** - HTTP 客户端后端实现
- 实现 `SandboxBackend` 接口
- 使用 `fileops` 模块（TarHandler）
- 通过 HTTP 调用远程服务

**职责**:
- 实现沙盒操作的具体逻辑
- 使用内部模块（security, fileops）
- 处理后端特定的细节

### 3. 内部模块

#### Security 模块

**CommandValidator** - 命令验证
- 验证命令是否安全
- 被 `LocalBackend` 使用
- **不对外暴露**，仅内部使用

**PathSanitizer** - 路径清理
- 防止路径遍历攻击
- 被 `LocalBackend` 使用
- **不对外暴露**，仅内部使用

#### FileOps 模块

**TarHandler** - Tar 文件处理
- 创建和解压 tar 归档
- 被 `LocalBackend`, `HTTPSandboxBackend`, `NoxRunnerClient` 使用
- **不对外暴露**，仅内部使用

## 模块使用关系

```
NoxRunnerClient
  ├─ LocalBackend
  │   ├─ CommandValidator (security)
  │   ├─ PathSanitizer (security)
  │   └─ TarHandler (fileops)
  │
  ├─ HTTPSandboxBackend
  │   └─ TarHandler (fileops)
  │
  └─ TarHandler (fileops)
```

## 设计原则

### 1. 分层清晰

- **Client 层**: 对外 API，用户直接使用
- **Backend 层**: 实现层，实现具体功能
- **内部模块**: 工具模块，被其他层使用

### 2. 职责分离

- **Client**: 提供统一接口和便捷方法
- **Backend**: 实现具体后端逻辑
- **Security**: 安全相关工具
- **FileOps**: 文件操作工具

### 3. 内部模块不对外暴露

- `security` 和 `fileops` 是内部实现细节
- 用户不应该直接导入这些模块
- 它们只被 `backend` 和 `client` 内部使用

### 4. 代码复用

- 公共逻辑提取到内部模块
- 避免代码重复
- 统一的安全检查和文件处理

## 使用建议

### ✅ 正确使用

```python
# 使用 Client（推荐）
from noxrunner import NoxRunnerClient
client = NoxRunnerClient(local_test=True)

# 直接使用 Backend（高级用法）
from noxrunner.backend.local import LocalBackend
backend = LocalBackend()
```

### ❌ 不推荐

```python
# 不要直接使用内部模块
from noxrunner.security import CommandValidator  # 不推荐
from noxrunner.fileops import TarHandler       # 不推荐（除非高级用法）

# 这些是内部实现细节，API 可能变化
```

## Client 使用 TarHandler

`NoxRunnerClient.download_workspace` 直接使用 `TarHandler` 解压 tar：

```python
# Client 内部使用 TarHandler
class NoxRunnerClient:
    def __init__(self, ...):
        self._tar_handler = TarHandler()  # 内部使用
    
    def download_workspace(self, ...):
        tar_data = self.download_files(...)
        # 直接使用 TarHandler 解压
        file_count = self._tar_handler.extract_tar(tar_data, local_path, allow_absolute=False)
```

**设计**:
- 简单直接，减少不必要的抽象层
- 职责清晰，TarHandler 专门处理 tar 操作
- 代码更易维护

## 未来扩展

添加新后端时：

```python
# 只需实现 Backend 接口
class K8sBackend(SandboxBackend):
    def __init__(self, ...):
        # 可以使用内部模块
        self.tar_handler = TarHandler()
    
    def upload_files(self, ...):
        # 使用 TarHandler
        tar_data = self.tar_handler.create_tar(files)
        # ... 调用 K8s API
```

**不需要**:
- 修改 Client
- 修改内部模块
- 影响其他后端
