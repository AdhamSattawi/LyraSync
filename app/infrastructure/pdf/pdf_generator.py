from abc import ABC, abstractmethod
from weasyprint import HTML
from asyncio import to_thread


class DocumentGenerator(ABC):
    @abstractmethod
    async def generate(self, html_content: str) -> bytes:
        raise NotImplementedError


class WeasyPrintGenerator(DocumentGenerator):
    def __init__(self) -> None:
        pass

    async def generate(self, html_content: str) -> bytes:
        """
        Generate a PDF from HTML content on a background thread.
        """
        html_obj = HTML(string=html_content)
        return await to_thread(html_obj.write_pdf)
