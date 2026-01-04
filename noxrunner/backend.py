"""
Backend interface for NoxRunner sandbox execution.

This module defines the abstract interface that all sandbox backends must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union


class SandboxBackend(ABC):
    """
    Abstract base class for sandbox execution backends.

    All backends (remote HTTP, local testing, etc.) must implement this interface.
    """

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the backend is healthy."""
        pass

    @abstractmethod
    def create_sandbox(
        self,
        session_id: str,
        ttl_seconds: int = 900,
        image: Optional[str] = None,
        cpu_limit: Optional[str] = None,
        memory_limit: Optional[str] = None,
        ephemeral_storage_limit: Optional[str] = None,
    ) -> dict:
        """Create or ensure a sandbox exists."""
        pass

    @abstractmethod
    def touch(self, session_id: str) -> bool:
        """Extend the TTL of a sandbox."""
        pass

    @abstractmethod
    def exec(
        self,
        session_id: str,
        cmd: List[str],
        workdir: str = "/workspace",
        env: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 30,
    ) -> dict:
        """Execute a command in the sandbox."""
        pass

    @abstractmethod
    def upload_files(
        self, session_id: str, files: Dict[str, Union[str, bytes]], dest: str = "/workspace"
    ) -> bool:
        """Upload files to the sandbox."""
        pass

    @abstractmethod
    def download_files(self, session_id: str, src: str = "/workspace") -> bytes:
        """Download files from the sandbox as a tar archive."""
        pass

    @abstractmethod
    def delete_sandbox(self, session_id: str) -> bool:
        """Delete a sandbox."""
        pass

    @abstractmethod
    def wait_for_pod_ready(self, session_id: str, timeout: int = 30, interval: int = 2) -> bool:
        """Wait for sandbox to be ready."""
        pass
