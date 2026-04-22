import os
import aiofiles
import aiofiles.os
from app.infrastructure.storage.storage_service import StorageService


class LocalStorageAdapter(StorageService):
    """
    Storage adapter for local development and testing.

    Uses aiofiles for all file I/O to avoid blocking the async event loop.
    Returns file:// paths — not publicly accessible URLs.

    Use STORAGE_BACKEND=local in .env for development.
    """

    def __init__(self, base_dir: str = "storage"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    async def upload(
        self,
        file_bytes: bytes,
        destination_path: str,
        content_type: str = "application/pdf",
    ) -> str:
        file_path = os.path.join(self.base_dir, destination_path)
        await aiofiles.os.makedirs(os.path.dirname(file_path), exist_ok=True)
        async with aiofiles.open(file_path, mode="wb") as f:
            await f.write(file_bytes)
        return f"file://{os.path.abspath(file_path)}"

    async def delete(self, file_path: str) -> None:
        await aiofiles.os.remove(file_path)

    async def get_public_url(self, file_path: str) -> str:
        return f"file://{os.path.abspath(file_path)}"

    async def download(self, file_path: str) -> bytes:
        async with aiofiles.open(file_path, mode="rb") as f:
            return await f.read()

    async def list_files(self, prefix: str = "") -> list[str]:
        target_dir = os.path.join(self.base_dir, prefix)
        entries = await aiofiles.os.listdir(target_dir)
        return [os.path.join(target_dir, name) for name in entries]
