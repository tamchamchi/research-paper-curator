from src.config import get_settings, MySQLSettings
from src.db.interfaces.base import BaseDatabase
from src.db.interfaces.mysql import MySQLDatabase


def make_database() -> BaseDatabase:
    """Factory function to create a database instance based on settings."""
    settings = get_settings()
    mysql_config = MySQLSettings(
        database_url=settings.mysql.database_url,
        echo_sql=settings.mysql.echo_sql,
        pool_size=settings.mysql.pool_size,
        max_overflow=settings.mysql.max_overflow,
    )
    database = MySQLDatabase(config=mysql_config)
    database.startup()
    return database
