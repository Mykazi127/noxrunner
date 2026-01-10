# NoxRunner 使用指南

## 概述

NoxRunner 是一个 Python 客户端库，用于与沙盒执行后端交互。它支持多种后端类型：
- **LocalBackend**: 本地文件系统后端（用于测试）
- **HTTPSandboxBackend**: HTTP 客户端后端（连接到远程服务）

## 安装

```bash
pip install noxrunner
```

或从源码安装：

```bash
git clone https://github.com/your-repo/noxrunner.git
cd noxrunner
pip install -e .
```

## 快速开始

### 使用 NoxRunnerClient（推荐）

`NoxRunnerClient` 提供了统一的接口，自动选择后端：

```python
from noxrunner import NoxRunnerClient

# 本地测试模式
client = NoxRunnerClient(local_test=True)

# 或连接到远程服务
client = NoxRunnerClient("http://127.0.0.1:8080")
```

### 直接使用后端

如果需要更多控制，可以直接使用后端：

```python
from noxrunner.backend.local import LocalBackend
from noxrunner.backend.http import HTTPSandboxBackend

# 本地后端
local_backend = LocalBackend(base_dir="/tmp")

# HTTP 后端
http_backend = HTTPSandboxBackend("http://127.0.0.1:8080", timeout=30)
```

## 基本使用

### 1. 创建沙盒

```python
from noxrunner import NoxRunnerClient

client = NoxRunnerClient(local_test=True)

# 创建沙盒
result = client.create_sandbox("my-session", ttl_seconds=900)
print(f"Sandbox: {result['podName']}")
print(f"Expires at: {result['expiresAt']}")
```

### 2. 执行命令

```python
# 执行简单命令
result = client.exec("my-session", ["echo", "Hello, World!"])
print(f"Exit code: {result['exitCode']}")
print(f"Output: {result['stdout']}")

# 执行 Python 代码
result = client.exec("my-session", ["python3", "-c", "print('Hello from Python!')"])
print(result['stdout'])

# 使用工作目录和环境变量
result = client.exec(
    "my-session",
    ["python3", "script.py"],
    workdir="/workspace",
    env={"PYTHONPATH": "/workspace"},
    timeout_seconds=60,
)
```

### 3. 上传文件

```python
# 上传单个文件
files = {
    "script.py": "print('Hello, World!')",
    "data.txt": "Some data",
}

client.upload_files("my-session", files)

# 上传二进制文件
files = {
    "image.png": b"\x89PNG\r\n\x1a\n...",  # PNG 文件内容
}

client.upload_files("my-session", files, dest="/workspace")
```

### 4. 下载文件

```python
# 下载为 tar 归档
tar_data = client.download_files("my-session", src="/workspace")

# 下载并解压到本地目录（推荐）
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmpdir:
    client.download_workspace("my-session", tmpdir)
    
    # 文件已解压到 tmpdir
    files = list(Path(tmpdir).glob("*"))
    for file in files:
        print(f"Downloaded: {file}")
```

### 5. 完整工作流示例

```python
from noxrunner import NoxRunnerClient
import tempfile
from pathlib import Path

# 创建客户端
client = NoxRunnerClient(local_test=True)

session_id = "my-task"

try:
    # 1. 创建沙盒
    client.create_sandbox(session_id)
    
    # 2. 上传文件
    files = {
        "main.py": """
def main():
    print("Hello from sandbox!")
    return 42

if __name__ == "__main__":
    result = main()
    print(f"Result: {result}")
""",
        "requirements.txt": "requests==2.31.0",
    }
    client.upload_files(session_id, files)
    
    # 3. 执行命令
    result = client.exec(session_id, ["python3", "main.py"])
    print(f"Exit code: {result['exitCode']}")
    print(f"Output:\n{result['stdout']}")
    
    # 4. 下载结果
    with tempfile.TemporaryDirectory() as tmpdir:
        client.download_workspace(session_id, tmpdir)
        
        # 处理下载的文件
        workspace = Path(tmpdir)
        for file in workspace.glob("*"):
            print(f"File: {file.name}")

finally:
    # 5. 清理
    client.delete_sandbox(session_id)
```

## 高级用法

### 使用 Shell 命令

```python
# 使用 exec_shell 执行 shell 命令字符串
result = client.exec_shell(
    "my-session",
    "ls -la | grep .py",
    workdir="/workspace",
)

# 使用 bash
result = client.exec_shell(
    "my-session",
    "echo $BASH_VERSION",
    shell="bash",
)
```

### 等待沙盒就绪

```python
# 等待沙盒准备就绪
ready = client.wait_for_pod_ready("my-session", timeout=60, interval=2)
if ready:
    print("Sandbox is ready!")
else:
    print("Sandbox not ready within timeout")
```

### 扩展沙盒 TTL

```python
# 延长沙盒生存时间
client.touch("my-session")
```

### 健康检查

```python
# 检查后端健康状态
if client.health_check():
    print("Backend is healthy")
else:
    print("Backend is not healthy")
```

## 后端类型

### LocalBackend

本地文件系统后端，用于测试和开发：

```python
from noxrunner.backend.local import LocalBackend

backend = LocalBackend(base_dir="/tmp")

# 所有操作都在本地文件系统执行
result = backend.exec("session-1", ["echo", "test"])
```

**警告**: LocalBackend 在本地环境执行命令，可能造成数据丢失或安全风险。仅用于测试！

### HTTPSandboxBackend

HTTP 客户端后端，连接到远程服务：

```python
from noxrunner.backend.http import HTTPSandboxBackend

backend = HTTPSandboxBackend("http://127.0.0.1:8080", timeout=30)

# 所有操作通过 HTTP API 调用远程服务
result = backend.exec("session-1", ["echo", "test"])
```

## 安全模块

### CommandValidator

验证命令是否安全：

```python
from noxrunner.security.command_validator import CommandValidator

validator = CommandValidator()

# 检查命令是否允许
if validator.validate(["echo", "hello"]):
    print("Command is safe")

# 检查命令是否被阻止
if validator.is_blocked("rm"):
    print("Command is blocked")
```

### PathSanitizer

清理路径，防止路径遍历攻击：

```python
from noxrunner.security.path_sanitizer import PathSanitizer
from pathlib import Path

sanitizer = PathSanitizer()
sandbox_path = Path("/tmp/sandbox")

# 清理路径
safe_path = sanitizer.sanitize("../../etc/passwd", sandbox_path)
# 返回: /tmp/sandbox/workspace (重定向到安全路径)

# 清理文件名
safe_name = sanitizer.sanitize_filename("/path/to/file.txt")
# 返回: "file.txt"
```

## 文件操作模块

### TarHandler

处理 Tar 归档：

```python
from noxrunner.fileops.tar_handler import TarHandler

handler = TarHandler()

# 从文件字典创建 tar
files = {"test.txt": "content"}
tar_data = handler.create_tar(files)

# 从目录创建 tar
from pathlib import Path
tar_data = handler.create_tar_from_directory(Path("/workspace"), Path("/workspace"))

# 解压 tar
handler.extract_tar(tar_data, Path("/output"))
```

## 错误处理

```python
from noxrunner import NoxRunnerClient, NoxRunnerError, NoxRunnerHTTPError

client = NoxRunnerClient("http://127.0.0.1:8080")

try:
    result = client.exec("session-1", ["echo", "test"])
except NoxRunnerHTTPError as e:
    print(f"HTTP error: {e.status_code} - {e.message}")
except NoxRunnerError as e:
    print(f"Error: {e}")
```

## 测试

### 运行所有测试

```bash
pytest tests/
```

### 运行单元测试

```bash
pytest tests/test_security.py tests/test_fileops.py tests/test_backend_local.py tests/test_backend_http.py
```

### 运行集成测试

```bash
# 本地后端集成测试（无需服务）
pytest tests/test_integration.py::TestLocalBackendIntegration

# HTTP 后端集成测试（需要运行的服务）
NOXRUNNER_ENABLE_INTEGRATION=1 NOXRUNNER_BASE_URL=http://127.0.0.1:8080 pytest tests/test_integration.py::TestHTTPSandboxBackendIntegration
```

## 最佳实践

1. **使用 NoxRunnerClient**: 优先使用 `NoxRunnerClient` 而不是直接使用后端
2. **错误处理**: 始终处理 `NoxRunnerError` 和 `NoxRunnerHTTPError`
3. **资源清理**: 使用 try/finally 确保删除沙盒
4. **超时设置**: 为长时间运行的任务设置适当的超时
5. **本地测试**: 开发时使用 `local_test=True`，生产环境使用 HTTP 后端

## 示例项目

查看 `examples/` 目录获取更多示例。
