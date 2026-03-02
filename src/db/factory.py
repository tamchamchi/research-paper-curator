from src.config import get_settings
from src.db.interfaces.base import BaseDatabase
from src.db.interfaces.mysql import MySQLDatabase, MySQLSettings


def make_database() -> BaseDatabase:
    """Factory function to create a database instance based on settings."""
    settings = get_settings()
    mysql_config = MySQLSettings(
        database_url=settings.mysql_url,
        echo_sql=settings.mysql_echo_sql,
        pool_size=settings.mysql_pool_size,
        max_overflow=settings.mysql_max_overflow,
    )
    return MySQLDatabase(config=mysql_config)
