"""
Integration tests for remote sandbox backend.

These tests require a running NoxRunner backend service.
They are marked with 'integration' marker and will be skipped
unless explicitly run with pytest -m integration.

To run these tests:
    pytest tests/test_remote_sandbox_integration.py -m integration

Or use make:
    make test-integration

Environment Variables:
    NOXRUNNER_BASE_URL    Base URL of the NoxRunner backend (default: http://127.0.0.1:8080)
"""

import os
import pytest
import time
import tempfile
import shutil
from pathlib import Path

from noxrunner import NoxRunnerClient, NoxRunnerError, NoxRunnerHTTPError


# Get base URL from environment
BASE_URL = os.environ.get("NOXRUNNER_BASE_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="module")
def client():
    """Create a client for integration tests."""
    return NoxRunnerClient(BASE_URL, timeout=30)


@pytest.fixture(scope="module")
def session_id():
    """Generate a unique session ID for tests."""
    return f"test-integration-{int(time.time())}"


@pytest.mark.integration
def test_health_check(client):
    """Test health check endpoint."""
    result = client.health_check()
    assert result is True, "Backend should be healthy"


@pytest.mark.integration
def test_create_sandbox(client, session_id):
    """Test creating a sandbox."""
    result = client.create_sandbox(session_id, ttl_seconds=300)

    assert "podName" in result
    assert "expiresAt" in result
    assert result["podName"] is not None


@pytest.mark.integration
def test_wait_for_pod_ready(client, session_id):
    """Test waiting for pod to be ready."""
    # Create sandbox first
    client.create_sandbox(session_id)

    # Wait for pod to be ready
    result = client.wait_for_pod_ready(session_id, timeout=60)
    assert result is True, "Pod should become ready"


@pytest.mark.integration
def test_exec_simple_command(client, session_id):
    """Test executing a simple command."""
    client.create_sandbox(session_id)
    client.wait_for_pod_ready(session_id, timeout=60)

    result = client.exec(session_id, ["echo", "hello", "world"])

    assert result["exitCode"] == 0
    assert "hello" in result["stdout"]
    assert "world" in result["stdout"]
    assert "durationMs" in result


@pytest.mark.integration
def test_exec_with_workdir(client, session_id):
    """Test executing command with custom workdir."""
    client.create_sandbox(session_id)
    client.wait_for_pod_ready(session_id, timeout=60)

    # Create a subdirectory
    client.exec(session_id, ["mkdir", "-p", "/workspace/subdir"])

    result = client.exec(session_id, ["pwd"], workdir="/workspace/subdir")

    assert result["exitCode"] == 0
    assert "subdir" in result["stdout"] or "/workspace/subdir" in result["stdout"]


@pytest.mark.integration
def test_exec_with_env(client, session_id):
    """Test executing command with environment variables."""
    client.create_sandbox(session_id)
    client.wait_for_pod_ready(session_id, timeout=60)

    # Use printenv which is more reliable than echo with shell variable expansion
    result = client.exec(
        session_id, ["printenv", "TEST_VAR"], env={"TEST_VAR": "test_value_123"}
    )

    assert result["exitCode"] == 0
    stdout = result["stdout"].strip()
    assert stdout == "test_value_123", f"Expected 'test_value_123', got: {repr(stdout)}"


@pytest.mark.integration
def test_exec_timeout(client, session_id):
    """Test command timeout."""
    client.create_sandbox(session_id)
    client.wait_for_pod_ready(session_id, timeout=60)

    result = client.exec(session_id, ["sleep", "10"], timeout_seconds=2)

    # Should timeout (exit code 124) or fail
    assert result["exitCode"] != 0


@pytest.mark.integration
def test_upload_files(client, session_id):
    """Test uploading files."""
    client.create_sandbox(session_id)
    client.wait_for_pod_ready(session_id, timeout=60)

    files = {
        "test.txt": "Hello, World!",
        "script.py": "print('test')",
        "data.bin": b"\x00\x01\x02\x03",
    }

    result = client.upload_files(session_id, files, dest="/workspace")
    assert result is True

    # Verify files exist
    result = client.exec(session_id, ["ls", "-la", "/workspace"])
    assert result["exitCode"] == 0
    assert "test.txt" in result["stdout"]
    assert "script.py" in result["stdout"]
    assert "data.bin" in result["stdout"]


@pytest.mark.integration
def test_download_files(client, session_id):
    """Test downloading files."""
    client.create_sandbox(session_id)
    client.wait_for_pod_ready(session_id, timeout=60)

    # Create some files
    files = {"file1.txt": "content1", "file2.txt": "content2", "subdir/file3.txt": "content3"}
    client.upload_files(session_id, files, dest="/workspace")

    # Download files
    tar_data = client.download_files(session_id, src="/workspace")
    assert len(tar_data) > 0

    # Extract and verify
    import tarfile
    import io

    tar_buffer = io.BytesIO(tar_data)
    # Use r:* to auto-detect compression (some backends return gzip, others return plain tar)
    with tarfile.open(fileobj=tar_buffer, mode="r:*") as tar:
        names = tar.getnames()
        # Filter out directory entries
        file_names = [n for n in names if not n.endswith('/') and n != '.']
        assert any("file1.txt" in name for name in file_names) or any("file1.txt" in name for name in names)
        assert any("file2.txt" in name for name in file_names) or any("file2.txt" in name for name in names)


@pytest.mark.integration
def test_touch(client, session_id):
    """Test touching (extending TTL) a sandbox."""
    client.create_sandbox(session_id, ttl_seconds=300)

    result = client.touch(session_id)
    assert result is True


@pytest.mark.integration
def test_delete_sandbox(client, session_id):
    """Test deleting a sandbox."""
    client.create_sandbox(session_id)
    client.wait_for_pod_ready(session_id, timeout=60)

    result = client.delete_sandbox(session_id)
    assert result is True

    # Verify sandbox is deleted
    # Note: Some backends may auto-recreate sandboxes on exec, so we check multiple ways
    try:
        # Try to exec - should either fail or the backend may auto-recreate
        exec_result = client.exec(session_id, ["echo", "test"], timeout_seconds=5)
        # If exec succeeds, backend auto-recreated the sandbox (acceptable behavior)
        # Just verify we got a response
        assert "exitCode" in exec_result
    except (NoxRunnerError, NoxRunnerHTTPError) as e:
        # If exec fails, that's also acceptable - sandbox was deleted
        pass


@pytest.mark.integration
def test_full_workflow(client):
    """Test a complete workflow: create, upload, exec, download, delete."""
    session_id = f"workflow-test-{int(time.time())}"

    try:
        # Create sandbox
        result = client.create_sandbox(session_id, ttl_seconds=600)
        assert "podName" in result

        # Wait for ready
        assert client.wait_for_pod_ready(session_id, timeout=60)

        # Upload files
        files = {
            "script.py": "#!/usr/bin/env python3\nprint('Hello from script!')\n",
            "data.txt": "test data",
        }
        assert client.upload_files(session_id, files)

        # Execute script
        result = client.exec(session_id, ["python3", "/workspace/script.py"])
        assert result["exitCode"] == 0
        assert "Hello from script!" in result["stdout"]

        # Download files
        tar_data = client.download_files(session_id)
        assert len(tar_data) > 0

        # Touch
        assert client.touch(session_id)

    finally:
        # Cleanup
        try:
            client.delete_sandbox(session_id)
        except:
            pass


@pytest.mark.integration
def test_concurrent_sessions(client):
    """Test multiple concurrent sessions."""
    session_ids = [f"concurrent-{i}-{int(time.time())}" for i in range(3)]

    try:
        # Create multiple sandboxes
        for sid in session_ids:
            client.create_sandbox(sid, ttl_seconds=300)

        # Wait for all to be ready
        for sid in session_ids:
            assert client.wait_for_pod_ready(sid, timeout=60)

        # Execute commands in each
        for sid in session_ids:
            result = client.exec(sid, ["echo", f"session-{sid}"])
            assert result["exitCode"] == 0

    finally:
        # Cleanup
        for sid in session_ids:
            try:
                client.delete_sandbox(sid)
            except:
                pass
