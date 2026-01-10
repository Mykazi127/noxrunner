# NoxRunner - 完整使用指南

## 概述

NoxRunner 是一个 Python 客户端库，用于与沙盒执行后端交互。它提供了清晰的架构，支持多种后端类型，代码结构清晰，易于扩展。

## 架构

```
noxrunner/
├── backend/          # 后端实现
│   ├── base.py       # 抽象基类 SandboxBackend
│   ├── local.py      # LocalBackend (本地文件系统后端)
│   └── http.py       # HTTPSandboxBackend (HTTP 客户端后端)
├── security/         # 安全模块
│   ├── command_validator.py  # 命令验证
│   └── path_sanitizer.py     # 路径清理
├── fileops/          # 文件操作模块
│   └── tar_handler.py        # Tar 文件处理
└── client.py         # NoxRunnerClient (统一客户端接口)
```

## 安装

```bash
# 从源码安装
git clone https://github.com/your-repo/noxrunner.git
cd noxrunner
pip install -e .

# 或使用 uv
uv sync
```

## 快速开始

### 基本使用

```python
from noxrunner import NoxRunnerClient

# 创建客户端（本地测试模式）
client = NoxRunnerClient(local_test=True)

# 或连接到远程服务
# client = NoxRunnerClient("http://127.0.0.1:8080")

# 创建沙盒
session_id = "my-session"
result = client.create_sandbox(session_id)
print(f"Sandbox: {result['podName']}")

# 执行命令
result = client.exec(session_id, ["echo", "Hello, World!"])
print(result["stdout"])

# 上传文件
client.upload_files(session_id, {
    "script.py": "print('Hello from NoxRunner!')"
})

# 下载工作区（推荐方式）
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmpdir:
    client.download_workspace(session_id, tmpdir)
    # 文件已解压到 tmpdir

# 清理
client.delete_sandbox(session_id)
```

## 后端类型

### LocalBackend

本地文件系统后端，用于测试和开发：

```python
from noxrunner.backend.local import LocalBackend

backend = LocalBackend(base_dir="/tmp")
backend.create_sandbox("session-1")
result = backend.exec("session-1", ["echo", "test"])
```

**警告**: LocalBackend 在本地环境执行命令，可能造成数据丢失或安全风险。仅用于测试！

### HTTPSandboxBackend

HTTP 客户端后端，连接到远程服务（如 Kubernetes 后端）：

```python
from noxrunner.backend.http import HTTPSandboxBackend

backend = HTTPSandboxBackend("http://127.0.0.1:8080", timeout=30)
backend.create_sandbox("session-1")
result = backend.exec("session-1", ["echo", "test"])
```

## 完整示例

### 示例 1: Python 脚本执行

```python
from noxrunner import NoxRunnerClient

client = NoxRunnerClient(local_test=True)
session_id = "python-example"

try:
    client.create_sandbox(session_id)
    
    # 上传 Python 脚本
    script = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")
"""
    client.upload_files(session_id, {"fib.py": script})
    
    # 执行脚本
    result = client.exec(session_id, ["python3", "fib.py"])
    print(result["stdout"])
    
finally:
    client.delete_sandbox(session_id)
```

### 示例 2: 文件同步工作流

```python
from noxrunner import NoxRunnerClient
import tempfile
from pathlib import Path

client = NoxRunnerClient(local_test=True)
session_id = "sync-example"

try:
    client.create_sandbox(session_id)
    
    # 上传多个文件
    files = {
        "main.py": "print('Hello from main')",
        "utils.py": "def helper(): return 42",
        "data.json": '{"key": "value"}',
    }
    client.upload_files(session_id, files)
    
    # 执行命令
    result = client.exec(session_id, ["python3", "main.py"])
    print(result["stdout"])
    
    # 下载工作区
    with tempfile.TemporaryDirectory() as tmpdir:
        client.download_workspace(session_id, tmpdir)
        
        # 处理下载的文件
        workspace = Path(tmpdir)
        for file in workspace.glob("*.py"):
            print(f"Downloaded: {file.name}")
    
finally:
    client.delete_sandbox(session_id)
```

## API 参考

### NoxRunnerClient

主要客户端类，提供统一接口：

- `create_sandbox(session_id, ttl_seconds=900, ...)` - 创建沙盒
- `exec(session_id, cmd, workdir="/workspace", env=None, timeout_seconds=30)` - 执行命令
- `exec_shell(session_id, command, workdir="/workspace", env=None, shell="sh")` - 执行 shell 命令
- `upload_files(session_id, files, dest="/workspace")` - 上传文件
- `download_files(session_id, src="/workspace")` - 下载文件（tar 格式）
- `download_workspace(session_id, local_dir, src="/workspace")` - 下载并解压工作区
- `delete_sandbox(session_id)` - 删除沙盒
- `wait_for_pod_ready(session_id, timeout=30, interval=2)` - 等待沙盒就绪
- `touch(session_id)` - 延长沙盒 TTL
- `health_check()` - 健康检查

### LocalBackend

本地后端实现：

```python
from noxrunner.backend.local import LocalBackend

backend = LocalBackend(base_dir="/tmp")
# 实现所有 SandboxBackend 接口
```

### HTTPSandboxBackend

HTTP 后端实现：

```python
from noxrunner.backend.http import HTTPSandboxBackend

backend = HTTPSandboxBackend("http://127.0.0.1:8080", timeout=30)
# 实现所有 SandboxBackend 接口
```

## 安全模块

### CommandValidator

验证命令是否安全：

```python
from noxrunner.security.command_validator import CommandValidator

validator = CommandValidator()
if validator.validate(["echo", "hello"]):
    print("Command is safe")
```

### PathSanitizer

清理路径，防止路径遍历：

```python
from noxrunner.security.path_sanitizer import PathSanitizer
from pathlib import Path

sanitizer = PathSanitizer()
safe_path = sanitizer.sanitize("../../etc/passwd", Path("/tmp/sandbox"))
# 返回: /tmp/sandbox/workspace (重定向到安全路径)
```

## 文件操作模块

### TarHandler

处理 Tar 归档：

```python
from noxrunner.fileops.tar_handler import TarHandler

handler = TarHandler()
files = {"test.txt": "content"}
tar_data = handler.create_tar(files)
handler.extract_tar(tar_data, Path("/output"))
```

## 测试

### 运行所有测试

```bash
# 单元测试
pytest tests/test_security.py tests/test_fileops.py tests/test_backend_local.py tests/test_backend_http.py

# 本地后端集成测试
pytest tests/test_integration.py::TestLocalBackendIntegration

# HTTP 后端集成测试（需要运行的服务）
NOXRUNNER_ENABLE_INTEGRATION=1 NOXRUNNER_BASE_URL=http://127.0.0.1:8080 pytest tests/test_integration.py::TestHTTPSandboxBackendIntegration
```

### 测试覆盖

- ✅ Security 模块：命令验证、路径清理
- ✅ FileOps 模块：Tar 处理、工作区同步
- ✅ LocalBackend：所有功能完整测试
- ✅ HTTPSandboxBackend：所有功能（使用 mock）
- ✅ 集成测试：完整工作流测试

## 文档

- [USAGE.md](USAGE.md) - 详细使用指南
- [EXAMPLES.md](EXAMPLES.md) - 更多示例
- [REFACTORING_PLAN.md](REFACTORING_PLAN.md) - 重构计划
- [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - 重构总结

## 未来扩展

架构支持轻松添加新后端：

- **K8sBackend**: 直接调用 Kubernetes API
- **DockerBackend**: 直接调用 Docker API

只需实现 `SandboxBackend` 接口即可。
