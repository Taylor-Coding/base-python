from pydantic import BaseModel


class ApiError(BaseModel):
    error_code: str
    error_message: str
    message: str

    @classmethod
    def of(cls, error_code: str, error_message: str) -> "ApiError":
        return cls(error_code=error_code, error_message=error_message, message=error_message)
