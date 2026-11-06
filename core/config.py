from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DEV_SECRET = "meditrack-local-7f4b9d2c8a1e6f3b5d7c9a2e4f6b8d1c"
INSECURE_SECRETS = {
    DEFAULT_DEV_SECRET,
    "replace-with-a-long-random-secret",
    "changeme",
    "secret",
}


class Settings(BaseSettings):
    app_name: str = "MediTrack"
    app_version: str = "1.0.0"
    app_description: str = "Agenda personal de medicamentos y tratamientos"

    # Entorno
    environment: str = Field(default="development")

    # Seguridad y JWT
    secret_key: str = Field(default=DEFAULT_DEV_SECRET)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=480)

    # Base de Datos
    database_url: str = Field(default="sqlite:///./meditrack.db")

    # Zona Horaria
    app_timezone: str = Field(default="America/Bogota")
    timezone_offset_hours: int = Field(default=-5)

    # Usuario Demo (Solo para desarrollo)
    demo_email: str | None = Field(default="demo@meditrack.app")
    demo_password: str | None = Field(default="MediTrack123!")
    demo_name: str = Field(default="María MediTrack")

    # Testing flag
    testing: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.is_production:
            if self.secret_key in INSECURE_SECRETS or len(self.secret_key.strip()) < 32:
                raise ValueError(
                    "Configuración insegura: en producción debes definir una SECRET_KEY "
                    "única y aleatoria de al menos 32 caracteres."
                )
        return self


settings = Settings()
