# NoxRunner 使用示例

## 基本示例

### 示例 1: 执行简单命令

```python
from noxrunner import NoxRunnerClient

# 创建客户端（本地测试模式）
client = NoxRunnerClient(local_test=True)

# 创建沙盒
session_id = "example-1"
client.create_sandbox(session_id)

# 执行命令
result = client.exec(session_id, ["echo", "Hello, World!"])
print(f"Output: {result['stdout']}")

# 清理
client.delete_sandbox(session_id)
```

### 示例 2: 上传和执行 Python 脚本

```python
from noxrunner import NoxRunnerClient

client = NoxRunnerClient(local_test=True)
session_id = "example-2"

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

### 示例 3: 文件同步

```python
from noxrunner import NoxRunnerClient
import tempfile
from pathlib import Path

client = NoxRunnerClient(local_test=True)
session_id = "example-3"

try:
    client.create_sandbox(session_id)
    
    # 上传多个文件
    files = {
        "main.py": "print('Hello from main')",
        "utils.py": "def helper(): return 42",
        "data.json": '{"key": "value"}',
    }
    client.upload_files(session_id, files)
    
    # 下载工作区到本地
    with tempfile.TemporaryDirectory() as tmpdir:
        client.download_workspace(session_id, tmpdir)
        
        # 处理下载的文件
        workspace = Path(tmpdir)
        for file in workspace.glob("*.py"):
            print(f"Downloaded: {file.name}")
            print(f"Content: {file.read_text()[:50]}...")
    
finally:
    client.delete_sandbox(session_id)
```

### 示例 4: 使用环境变量

```python
from noxrunner import NoxRunnerClient

client = NoxRunnerClient(local_test=True)
session_id = "example-4"

try:
    client.create_sandbox(session_id)
    
    # 使用环境变量执行命令
    result = client.exec(
        session_id,
        ["sh", "-c", "echo $MY_VAR && echo $ANOTHER_VAR"],
        env={
            "MY_VAR": "Hello",
            "ANOTHER_VAR": "World",
        },
    )
    print(result["stdout"])
    
finally:
    client.delete_sandbox(session_id)
```

### 示例 5: 使用 Shell 命令

```python
from noxrunner import NoxRunnerClient

client = NoxRunnerClient(local_test=True)
session_id = "example-5"

try:
    client.create_sandbox(session_id)
    
    # 使用 exec_shell 执行 shell 命令字符串
    result = client.exec_shell(
        session_id,
        "ls -la | head -5",
        workdir="/workspace",
    )
    print(result["stdout"])
    
    # 使用管道和重定向
    result = client.exec_shell(
        session_id,
        "echo 'test' > output.txt && cat output.txt",
    )
    print(result["stdout"])
    
finally:
    client.delete_sandbox(session_id)
```

## 高级示例

### 示例 6: 完整工作流

```python
from noxrunner import NoxRunnerClient
import tempfile
from pathlib import Path

def run_task_in_sandbox(task_files: dict, command: list):
    """在沙盒中运行任务的完整工作流"""
    client = NoxRunnerClient(local_test=True)
    session_id = f"task-{id(task_files)}"
    
    try:
        # 1. 创建沙盒
        client.create_sandbox(session_id, ttl_seconds=1800)
        print(f"✓ Created sandbox: {session_id}")
        
        # 2. 等待就绪
        if not client.wait_for_pod_ready(session_id, timeout=30):
            raise Exception("Sandbox not ready")
        print("✓ Sandbox is ready")
        
        # 3. 上传文件
        client.upload_files(session_id, task_files)
        print(f"✓ Uploaded {len(task_files)} files")
        
        # 4. 执行命令
        result = client.exec(session_id, command, timeout_seconds=300)
        print(f"✓ Command executed (exit code: {result['exitCode']})")
        
        if result["exitCode"] != 0:
            print(f"Error: {result['stderr']}")
            return None
        
        # 5. 下载结果
        with tempfile.TemporaryDirectory() as tmpdir:
            client.download_workspace(session_id, tmpdir)
            print(f"✓ Downloaded workspace to {tmpdir}")
            
            return {
                "output": result["stdout"],
                "workspace": Path(tmpdir),
            }
    
    finally:
        # 6. 清理
        client.delete_sandbox(session_id)
        print("✓ Cleaned up sandbox")

# 使用示例
task_files = {
    "main.py": """
import sys
import json

data = {"result": 42, "message": "Success"}
print(json.dumps(data))
""",
}

result = run_task_in_sandbox(task_files, ["python3", "main.py"])
if result:
    print(f"Output: {result['output']}")
```

### 示例 7: 直接使用后端

```python
from noxrunner.backend.local import LocalBackend
from noxrunner.backend.http import HTTPSandboxBackend

# 使用本地后端
local_backend = LocalBackend(base_dir="/tmp")

session_id = "direct-backend-example"
local_backend.create_sandbox(session_id)

result = local_backend.exec(session_id, ["echo", "test"])
print(result["stdout"])

local_backend.delete_sandbox(session_id)

# 使用 HTTP 后端
http_backend = HTTPSandboxBackend("http://127.0.0.1:8080")
http_backend.create_sandbox(session_id)
# ... 使用方式相同
```

### 示例 8: 错误处理

```python
from noxrunner import NoxRunnerClient, NoxRunnerError, NoxRunnerHTTPError

client = NoxRunnerClient("http://127.0.0.1:8080")
session_id = "error-handling-example"

try:
    # 健康检查
    if not client.health_check():
        print("Backend is not healthy")
        exit(1)
    
    # 创建沙盒
    client.create_sandbox(session_id)
    
    # 执行可能失败的命令
    result = client.exec(session_id, ["python3", "nonexistent.py"])
    
    if result["exitCode"] != 0:
        print(f"Command failed: {result['stderr']}")
    
except NoxRunnerHTTPError as e:
    print(f"HTTP error: {e.status_code} - {e.message}")
except NoxRunnerError as e:
    print(f"Error: {e}")
finally:
    try:
        client.delete_sandbox(session_id)
    except Exception:
        pass
```

## 与 Titan 集成示例

```python
from noxrunner import NoxRunnerClient
from titan.runtime.sandbox_adapter import SandboxAdapter
from titan.config.models import SandboxConfig

# Titan 使用 NoxRunner 的方式
sandbox_config = SandboxConfig(
    base_url=None,  # None 表示使用 local_test
    local_test=True,
)

adapter = SandboxAdapter(sandbox_config, session_id="titan-task")
adapter.initialize()

# 上传工作区
adapter.upload_workspace("/path/to/workspace")

# 执行命令
result = adapter.exec_shell("python3 script.py")

# 下载工作区（同步文件回本地）
adapter.download_workspace("/path/to/workspace")
```

## 更多示例

查看 `examples/` 目录获取更多完整示例。
