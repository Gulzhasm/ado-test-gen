from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ado_org: str
    ado_project: str
    ado_pat: str

    ado_test_plan_id: str | None = None
    ado_test_suite_id: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
    