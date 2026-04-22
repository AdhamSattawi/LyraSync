from abc import ABC, abstractmethod


class StorageService(ABC):
    @abstractmethod
    async def upload(
        self,
        file_bytes: bytes,
        destination_path: str,
        content_type: str = "application/pdf",
    ) -> str:
        """Upload and return a publicly accessible URL."""
        pass

    @abstractmethod
    async def delete(self, file_path: str) -> None:
        """Delete a file."""
        pass

    @abstractmethod
    async def get_public_url(self, file_path: str) -> str:
        """Get a publicly accessible URL for a file."""
        pass

    @abstractmethod
    async def download(self, file_path: str) -> bytes:
        """Download a file."""
        pass

    @abstractmethod
    async def list_files(self, prefix: str = "") -> list[str]:
        """List files in a directory."""
        pass
