from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_model: str = ""
    kubeconfig_path: str = ""
    insforge_url: str = ""
    insforge_anon_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
