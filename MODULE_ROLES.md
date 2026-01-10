# NoxRunner 模块角色说明

## 架构层次

### 1. 对外 API 层

**NoxRunnerClient** (`noxrunner/client.py`)
- **角色**: 对外暴露的统一接口
- **用户**: 最终用户（如 titan）
- **职责**: 
  - 提供统一、简洁的 API
  - 自动选择后端
  - 提供便捷方法（如 `download_workspace`）

**使用方式**:
```python
from noxrunner import NoxRunnerClient
client = NoxRunnerClient(local_test=True)
```

### 2. Backend 实现层

**LocalBackend** (`noxrunner/backend/local.py`)
- **角色**: 本地后端实现
- **用户**: NoxRunnerClient（内部使用）
- **职责**: 实现本地文件系统沙盒

**HTTPSandboxBackend** (`noxrunner/backend/http.py`)
- **角色**: HTTP 客户端后端实现
- **用户**: NoxRunnerClient（内部使用）
- **职责**: 通过 HTTP 调用远程服务

**使用方式**:
```python
# 高级用法，直接使用后端
from noxrunner.backend.local import LocalBackend
backend = LocalBackend()
```

### 3. 内部工具模块

#### Security 模块 (`noxrunner/security/`)

**CommandValidator** - 命令验证
- **角色**: 内部工具，被 LocalBackend 使用
- **用户**: LocalBackend（内部）
- **职责**: 验证命令是否安全

**PathSanitizer** - 路径清理
- **角色**: 内部工具，被 LocalBackend 使用
- **用户**: LocalBackend（内部）
- **职责**: 防止路径遍历攻击

**使用方式**:
```python
# 内部使用，不对外暴露
# LocalBackend 内部使用
self.validator = CommandValidator()
self.sanitizer = PathSanitizer()
```

#### FileOps 模块 (`noxrunner/fileops/`)

**TarHandler** - Tar 文件处理
- **角色**: 内部工具，被 Backend 和 Client 使用
- **用户**: LocalBackend, HTTPSandboxBackend, NoxRunnerClient（内部）
- **职责**: 创建和解压 tar 归档

**使用方式**:
```python
# 内部使用，不对外暴露
# NoxRunnerClient 内部使用
self._tar_handler = TarHandler()
file_count = self._tar_handler.extract_tar(tar_data, local_path, allow_absolute=False)
```

## 模块可见性

### ✅ 对外暴露（Public API）

```python
from noxrunner import NoxRunnerClient
from noxrunner.backend.local import LocalBackend
from noxrunner.backend.http import HTTPSandboxBackend
```

### ⚠️ 内部模块（Internal，不推荐直接使用）

```python
# 这些是内部实现细节，API 可能变化
from noxrunner.security import CommandValidator  # 不推荐
from noxrunner.fileops import TarHandler         # 不推荐（除非高级用法）
```

## Client 使用 TarHandler

`NoxRunnerClient.download_workspace` 直接使用 `TarHandler` 解压 tar：

```python
class NoxRunnerClient:
    def __init__(self, ...):
        # 内部使用 TarHandler
        self._tar_handler = TarHandler()
    
    def download_workspace(self, session_id, local_dir, src="/workspace"):
        # 1. 从 backend 下载 tar
        tar_data = self.download_files(session_id, src)
        
        # 2. 直接使用 TarHandler 解压
        file_count = self._tar_handler.extract_tar(
            tar_data=tar_data,
            dest=local_path,
            allow_absolute=False,
        )
        return file_count > 0
```

**设计**:
- ✅ 简单直接，减少不必要的抽象层
- ✅ 职责清晰，TarHandler 专门处理 tar 操作
- ✅ 代码更易维护

## 设计原则

1. **Client 对外，Backend 实现，内部模块工具化**
   - Client: 对外 API
   - Backend: 实现具体功能
   - Security/FileOps: 内部工具

2. **内部模块不对外暴露**
   - 用户不应该直接导入 `security` 或 `fileops`
   - 这些是实现细节，API 可能变化

3. **代码复用**
   - 公共逻辑提取到内部模块
   - 避免代码重复
   - 统一的安全检查和文件处理

## 总结

- ✅ **Client**: 对外 API，用户直接使用
- ✅ **Backend**: 实现层，实现具体功能
- ✅ **Security**: 内部工具，被 Backend 使用
- ✅ **FileOps**: 内部工具，被 Backend 和 Client 使用
  - **TarHandler**: 被 Backend 和 Client 使用，处理 tar 操作
