class DomainError(ValueError):
    """Excepción de negocio con código de estado HTTP asociado."""

    def __init__(self, detail: str, status_code: int = 422):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class NotFoundError(DomainError):
    """Recurso de dominio no encontrado (HTTP 404)."""

    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=404)


class ConflictError(DomainError):
    """Conflicto de estado en regla de negocio (HTTP 409)."""

    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=409)
