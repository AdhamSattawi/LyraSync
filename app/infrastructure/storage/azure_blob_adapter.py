from datetime import datetime, timedelta, timezone

from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import generate_blob_sas, BlobSasPermissions

from app.infrastructure.storage.storage_service import StorageService


class AzureBlobAdapter(StorageService):
    """
    Production storage adapter backed by Azure Blob Storage.

    All I/O uses the async Azure SDK (azure.storage.blob.aio) to avoid
    blocking the FastAPI event loop.

    upload() returns a time-limited Shared Access Signature (SAS) URL
    so that documents can be shared with clients securely without making
    the entire container public.

    Use STORAGE_BACKEND=azure in .env for production.
    """

    def __init__(
        self,
        connection_string: str,
        container_name: str,
        account_name: str,
        account_key: str,
        sas_expiry_hours: int = 24,
    ):
        self.connection_string = connection_string
        self.container_name = container_name
        self.account_name = account_name
        self.account_key = account_key
        self.sas_expiry_hours = sas_expiry_hours

    def _get_client(self) -> BlobServiceClient:
        """Create a fresh async client per operation (avoids connection state issues)."""
        return BlobServiceClient.from_connection_string(self.connection_string)

    def _generate_sas_url(self, blob_name: str) -> str:
        """
        Generate a time-limited SAS URL for a blob.

        SAS tokens are computed locally (no network call) so this is safe
        to call synchronously inside an async method.
        """
        expiry = datetime.now(timezone.utc) + timedelta(hours=self.sas_expiry_hours)
        sas_token = generate_blob_sas(
            account_name=self.account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=self.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry,
        )
        return (
            f"https://{self.account_name}.blob.core.windows.net"
            f"/{self.container_name}/{blob_name}?{sas_token}"
        )

    async def upload(
        self,
        file_bytes: bytes,
        destination_path: str,
        content_type: str = "application/pdf",
    ) -> str:
        async with self._get_client() as service_client:
            container_client = service_client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(destination_path)
            await blob_client.upload_blob(
                file_bytes,
                overwrite=True,
                content_settings={"content_type": content_type},
            )
        # Return a SAS URL — blobs are private by default
        return self._generate_sas_url(destination_path)

    async def delete(self, file_path: str) -> None:
        async with self._get_client() as service_client:
            container_client = service_client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(file_path)
            await blob_client.delete_blob()

    async def get_public_url(self, file_path: str) -> str:
        """Returns a fresh SAS URL for an existing blob."""
        return self._generate_sas_url(file_path)

    async def download(self, file_path: str) -> bytes:
        async with self._get_client() as service_client:
            container_client = service_client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(file_path)
            stream = await blob_client.download_blob()
            return await stream.readall()

    async def list_files(self, prefix: str = "") -> list[str]:
        async with self._get_client() as service_client:
            container_client = service_client.get_container_client(self.container_name)
            return [
                blob.name
                async for blob in container_client.list_blobs(name_starts_with=prefix)
            ]
