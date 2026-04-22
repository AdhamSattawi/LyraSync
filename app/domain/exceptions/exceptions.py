class DomainException(Exception):
    def __init__(self, message: str, name: str = "Domain Error") -> None:
        self.message = message
        self.name = name
        super().__init__(self.message)


class TradesmanNotFoundError(DomainException):
    def __init__(self, tradesman_id: str) -> None:
        message = f"Tradesman with ID {tradesman_id} not found"
        super().__init__(message, "Tradesman Not Found Error")


class ConfigurationError(DomainException):
    def __init__(self, message: str) -> None:
        super().__init__(message, "Configuration Error")


class WhatsAppIntegrationError(DomainException):
    def __init__(self, message: str) -> None:
        super().__init__(message, "WhatsApp Integration Error")


class WhatsAppMessageError(DomainException):
    def __init__(self, message: str) -> None:
        super().__init__(message, "WhatsApp Message Error")


class AIError(DomainException):
    def __init__(self, message: str) -> None:
        super().__init__(message, "AI Error")


class AIAnalysisError(AIError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "AI Analysis Error")


class PDFGenerationError(DomainException):
    def __init__(self, message: str) -> None:
        super().__init__(message, "PDF Generation Error")


class PDFProcessingError(DomainException):
    def __init__(self, message: str) -> None:
        super().__init__(message, "PDF Processing Error")


class PDFValidationError(DomainException):
    def __init__(self, message: str) -> None:
        super().__init__(message, "PDF Validation Error")
