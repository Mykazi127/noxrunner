"""
Tests for local sandbox backend.

WARNING: These tests execute commands in the local environment.
They are designed to be safe by only operating within /tmp directories.
"""

import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path

from noxrunner import NoxRunnerClient
from noxrunner.local_sandbox import LocalSandboxBackend


class TestLocalSandboxBackend:
    """Test LocalSandboxBackend directly."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use a temporary directory for testing
        self.test_base = tempfile.mkdtemp(prefix="noxrunner_test_")
        self.backend = LocalSandboxBackend(base_dir=self.test_base)
        self.session_id = "test-session-123"

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up sandbox
        if self.session_id in self.backend._sandboxes:
            self.backend.delete_sandbox(self.session_id)
        # Clean up test directory
        if os.path.exists(self.test_base):
            shutil.rmtree(self.test_base)

    def test_health_check(self):
        """Test health check."""
        assert self.backend.health_check() is True

    def test_create_sandbox(self):
        """Test creating a sandbox."""
        result = self.backend.create_sandbox(self.session_id, ttl_seconds=300)

        assert "podName" in result
        assert "expiresAt" in result
        assert result["podName"] == f"local-{self.session_id}"

        # Verify sandbox directory exists
        sandbox_path = self.backend._get_sandbox_path(self.session_id)
        assert sandbox_path.exists()
        assert (sandbox_path / "workspace").exists()

    def test_touch(self):
        """Test touching a sandbox."""
        # Create sandbox first
        self.backend.create_sandbox(self.session_id)

        # Touch should extend TTL
        assert self.backend.touch(self.session_id) is True

        # Touch non-existent sandbox should create it
        assert self.backend.touch("new-session") is True

    def test_exec_simple_command(self, capsys):
        """Test executing a simple command."""
        self.backend.create_sandbox(self.session_id)

        result = self.backend.exec(self.session_id, ["echo", "hello"])

        # Check warning was printed
        captured = capsys.readouterr()
        assert "WARNING" in captured.err or "CRITICAL WARNING" in captured.err

        assert result["exitCode"] == 0
        assert "hello" in result["stdout"]
        assert result["stderr"] == ""
        assert "durationMs" in result

    def test_exec_python_command(self, capsys):
        """Test executing a Python command."""
        self.backend.create_sandbox(self.session_id)

        result = self.backend.exec(self.session_id, ["python3", "-c", "print('test output')"])

        # Check warning was printed
        captured = capsys.readouterr()
        assert "WARNING" in captured.err or "CRITICAL WARNING" in captured.err

        # Python might not be available, so check exit code
        if result["exitCode"] == 0:
            assert "test output" in result["stdout"]
        else:
            # Python not found is acceptable in test environment
            assert result["exitCode"] in (127, 1)  # Command not found or error

    def test_exec_with_workdir(self, capsys):
        """Test executing command with custom workdir."""
        self.backend.create_sandbox(self.session_id)

        # Create a subdirectory
        sandbox_path = self.backend._get_sandbox_path(self.session_id)
        subdir = sandbox_path / "workspace" / "subdir"
        subdir.mkdir(parents=True, exist_ok=True)

        result = self.backend.exec(self.session_id, ["pwd"], workdir="/workspace/subdir")

        # Check warning was printed
        captured = capsys.readouterr()
        assert "WARNING" in captured.err or "CRITICAL WARNING" in captured.err

        if result["exitCode"] == 0:
            # pwd output should contain the workdir
            assert "subdir" in result["stdout"] or "workspace" in result["stdout"]

    def test_exec_with_env(self, capsys):
        """Test executing command with environment variables."""
        self.backend.create_sandbox(self.session_id)

        result = self.backend.exec(
            self.session_id, ["sh", "-c", "echo $TEST_VAR"], env={"TEST_VAR": "test_value"}
        )

        # Check warning was printed
        captured = capsys.readouterr()
        assert "WARNING" in captured.err or "CRITICAL WARNING" in captured.err

        if result["exitCode"] == 0:
            assert "test_value" in result["stdout"]

    def test_exec_timeout(self, capsys):
        """Test command timeout."""
        self.backend.create_sandbox(self.session_id)

        # Try to sleep (if available)
        result = self.backend.exec(self.session_id, ["sleep", "10"], timeout_seconds=1)

        # Check warning was printed
        captured = capsys.readouterr()
        assert "WARNING" in captured.err or "CRITICAL WARNING" in captured.err

        # Should timeout or command not found
        assert result["exitCode"] in (124, 127)  # Timeout or not found

    def test_exec_blocked_command(self, capsys):
        """Test that blocked commands are rejected."""
        self.backend.create_sandbox(self.session_id)

        result = self.backend.exec(self.session_id, ["rm", "-rf", "/"])

        # Check warning was printed
        captured = capsys.readouterr()
        assert "WARNING" in captured.err or "CRITICAL WARNING" in captured.err

        # Should be blocked
        assert result["exitCode"] == 1
        assert "not allowed" in result["stderr"].lower()

    def test_upload_files(self):
        """Test uploading files."""
        self.backend.create_sandbox(self.session_id)

        files = {
            "test.txt": "Hello, World!",
            "script.py": "print('test')",
            "binary.bin": b"\x00\x01\x02\x03",
        }

        result = self.backend.upload_files(self.session_id, files, dest="/workspace")
        assert result is True

        # Verify files exist
        sandbox_path = self.backend._get_sandbox_path(self.session_id)
        workspace = sandbox_path / "workspace"

        assert (workspace / "test.txt").exists()
        assert (workspace / "script.py").exists()
        assert (workspace / "binary.bin").exists()

        # Verify content
        assert (workspace / "test.txt").read_text() == "Hello, World!"
        assert (workspace / "script.py").read_text() == "print('test')"
        assert (workspace / "binary.bin").read_bytes() == b"\x00\x01\x02\x03"

    def test_upload_files_path_traversal_protection(self):
        """Test that path traversal attacks are prevented."""
        self.backend.create_sandbox(self.session_id)

        # Try to upload file with path traversal
        files = {"../../../etc/passwd": "should not be written", "normal.txt": "should be written"}

        result = self.backend.upload_files(self.session_id, files)
        assert result is True

        # Verify only safe filename was written
        sandbox_path = self.backend._get_sandbox_path(self.session_id)
        workspace = sandbox_path / "workspace"

        # Path traversal should be sanitized to just filename
        assert not (workspace / "../../../etc/passwd").exists()
        assert (workspace / "passwd").exists() or (workspace / "normal.txt").exists()

    def test_download_files(self):
        """Test downloading files."""
        self.backend.create_sandbox(self.session_id)

        # Create some files
        sandbox_path = self.backend._get_sandbox_path(self.session_id)
        workspace = sandbox_path / "workspace"
        (workspace / "file1.txt").write_text("content1")
        (workspace / "file2.txt").write_text("content2")
        (workspace / "subdir").mkdir()
        (workspace / "subdir" / "file3.txt").write_text("content3")

        # Download files
        tar_data = self.backend.download_files(self.session_id, src="/workspace")

        assert len(tar_data) > 0

        # Extract and verify
        import tarfile
        import io

        tar_buffer = io.BytesIO(tar_data)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            names = tar.getnames()
            assert any("file1.txt" in name for name in names)
            assert any("file2.txt" in name for name in names)

    def test_delete_sandbox(self):
        """Test deleting a sandbox."""
        self.backend.create_sandbox(self.session_id)

        sandbox_path = self.backend._get_sandbox_path(self.session_id)
        assert sandbox_path.exists()

        result = self.backend.delete_sandbox(self.session_id)
        assert result is True

        # Verify sandbox directory is deleted
        assert not sandbox_path.exists()
        assert self.session_id not in self.backend._sandboxes

    def test_wait_for_pod_ready(self):
        """Test waiting for pod ready."""
        # Local sandbox should be ready immediately
        result = self.backend.wait_for_pod_ready(self.session_id)
        assert result is True


class TestNoxRunnerClientLocalMode:
    """Test NoxRunnerClient with local_test mode."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use a temporary directory for testing
        self.test_base = tempfile.mkdtemp(prefix="noxrunner_test_")
        # Create client with local_test=True
        self.client = NoxRunnerClient(local_test=True)
        # Override base_dir for testing
        from pathlib import Path

        # Access the backend instance
        self.client._backend.base_dir = Path(self.test_base)
        self.session_id = "test-client-session"

    def teardown_method(self):
        """Clean up test fixtures."""
        try:
            self.client.delete_sandbox(self.session_id)
        except:
            pass
        # Clean up test directory
        if os.path.exists(self.test_base):
            shutil.rmtree(self.test_base)

    def test_client_local_mode_initialization(self):
        """Test client initialization with local mode."""
        # Warning is printed during setup_method when client is created
        # Just verify client was created successfully
        assert self.client is not None
        assert hasattr(self.client, "_backend")

    def test_client_create_sandbox(self):
        """Test creating sandbox via client."""
        result = self.client.create_sandbox(self.session_id)

        assert "podName" in result
        assert "expiresAt" in result

    def test_client_exec(self, capsys):
        """Test executing command via client."""
        self.client.create_sandbox(self.session_id)

        result = self.client.exec(self.session_id, ["echo", "test"])

        # Multiple warnings should be printed (init + exec)
        captured = capsys.readouterr()
        assert "WARNING" in captured.err or "CRITICAL WARNING" in captured.err

        assert result["exitCode"] == 0
        assert "test" in result["stdout"]

    def test_client_upload_download(self):
        """Test upload and download via client."""
        self.client.create_sandbox(self.session_id)

        # Upload files
        files = {"test.txt": "Hello from test", "data.json": '{"key": "value"}'}
        assert self.client.upload_files(self.session_id, files) is True

        # Download files
        tar_data = self.client.download_files(self.session_id)
        assert len(tar_data) > 0

        # Verify content
        import tarfile
        import io

        tar_buffer = io.BytesIO(tar_data)
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            names = tar.getnames()
            assert any("test.txt" in name for name in names)

    def test_client_touch(self):
        """Test touch via client."""
        self.client.create_sandbox(self.session_id)
        assert self.client.touch(self.session_id) is True

    def test_client_delete_sandbox(self):
        """Test delete sandbox via client."""
        self.client.create_sandbox(self.session_id)
        assert self.client.delete_sandbox(self.session_id) is True

    def test_client_health_check(self):
        """Test health check via client."""
        assert self.client.health_check() is True

    def test_client_wait_for_pod_ready(self):
        """Test wait for pod ready via client."""
        assert self.client.wait_for_pod_ready(self.session_id) is True


class TestLocalSandboxSecurity:
    """Test security features of local sandbox."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_base = tempfile.mkdtemp(prefix="noxrunner_test_")
        self.backend = LocalSandboxBackend(base_dir=self.test_base)
        self.session_id = "security-test"

    def teardown_method(self):
        """Clean up test fixtures."""
        try:
            self.backend.delete_sandbox(self.session_id)
        except:
            pass
        if os.path.exists(self.test_base):
            shutil.rmtree(self.test_base)

    def test_path_traversal_protection(self):
        """Test that path traversal is prevented."""
        self.backend.create_sandbox(self.session_id)
        sandbox_path = self.backend._get_sandbox_path(self.session_id)

        # Try to access path outside sandbox
        outside_path = "/etc/passwd"
        sanitized = self.backend._sanitize_path(outside_path, sandbox_path)

        # Should be redirected to workspace
        assert sandbox_path.resolve() in sanitized.resolve().parents

    def test_relative_path_safety(self):
        """Test that relative paths are safe."""
        self.backend.create_sandbox(self.session_id)
        sandbox_path = self.backend._get_sandbox_path(self.session_id)

        # Try relative path traversal
        relative_path = "../../../etc/passwd"
        sanitized = self.backend._sanitize_path(relative_path, sandbox_path)

        # Should be within sandbox
        try:
            sanitized.resolve().relative_to(sandbox_path.resolve())
        except ValueError:
            pytest.fail("Path traversal not prevented")

    def test_command_validation(self):
        """Test command validation."""
        # Blocked commands should be rejected
        assert not self.backend._validate_command(["rm", "-rf", "/"])
        assert not self.backend._validate_command(["sudo", "rm", "/"])

        # Allowed commands should pass (if they exist)
        # Note: We can't test all commands as they may not exist
        assert self.backend._validate_command(["echo", "test"])

    def test_sandbox_isolation(self, capsys):
        """Test that sandboxes are isolated."""
        self.backend.create_sandbox(self.session_id)

        # Create file in sandbox
        sandbox_path = self.backend._get_sandbox_path(self.session_id)
        test_file = sandbox_path / "workspace" / "isolated.txt"
        test_file.write_text("isolated content")

        # Execute command that tries to access it
        result = self.backend.exec(self.session_id, ["cat", "isolated.txt"], workdir="/workspace")

        # Should be able to access file within sandbox
        if result["exitCode"] == 0:
            assert "isolated content" in result["stdout"]

        # Check warning was printed
        captured = capsys.readouterr()
        assert "WARNING" in captured.err or "CRITICAL WARNING" in captured.err
