from src.config import Settings


def test_settings_initialization():
    """Test that Settings can be initialized."""

    settings = Settings()

    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.service_name == "rag-api"
    assert settings.debug is False


def test_settings_mysql_defaults():
    """Test MySQL default settings."""
    settings = Settings()

    assert "mysql+pymysql://" in settings.mysql_database_url
    assert settings.mysql_echo_sql is False
    assert settings.mysql_max_overflow == 0
    assert settings.mysql_pool_size == 20


def test_settings_ollama_defaults():
    """Test Ollama default configuration."""
    settings = Settings()

    # In Docker environment, this should be ollama service host
    assert settings.ollama_host in ["http://localhost:11434", "http://ollama:11434"]
