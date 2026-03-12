import os
from dotenv import load_dotenv


class Settings:
    """Centralized configuration loaded from environment variables."""

    def __init__(self) -> None:
        load_dotenv()

        # Provider selection: "openrouter" or "openai"
        self.provider: str = os.getenv("PROVIDER", "openai").lower()

        # OpenRouter
        self.openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_base_url: str = "https://openrouter.ai/api/v1"

        # OpenAI
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

        # Langfuse
        self.langfuse_public_key: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        self.langfuse_secret_key: str = os.getenv("LANGFUSE_SECRET_KEY", "")
        self.langfuse_host: str = os.getenv(
            "LANGFUSE_HOST", "https://challenges.reply.com/langfuse"
        )

        # Team
        self.team_name: str = os.getenv("TEAM_NAME", "tutorial")

        # Default model
        self.default_model_id: str = os.getenv("MODEL_ID", "gpt-5-mini")
        self.default_temperature: float = float(os.getenv("TEMPERATURE", "0.7"))
        self.default_max_tokens: int = int(os.getenv("MAX_TOKENS", "1000"))

    def validate(self) -> None:
        """Raise if essential keys are missing."""
        missing = []
        
        if self.provider not in ["openrouter", "openai"]:
            raise EnvironmentError(
                f"Invalid PROVIDER: {self.provider}. Must be 'openrouter' or 'openai'."
            )
        
        if self.provider == "openrouter" and not self.openrouter_api_key:
            missing.append("OPENROUTER_API_KEY")
        elif self.provider == "openai" and not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        
        if not self.langfuse_public_key:
            missing.append("LANGFUSE_PUBLIC_KEY")
        if not self.langfuse_secret_key:
            missing.append("LANGFUSE_SECRET_KEY")
        
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
