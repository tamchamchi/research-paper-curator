import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from src.db.interfaces.base import BaseDatabase
from src.config import MySQLSettings

logger = logging.getLogger(__name__)


Base = declarative_base()


class MySQLDatabase(BaseDatabase):
    """MySQL database implementation using SQLAlchemy."""

    def __init__(self, config: MySQLSettings):
        self.config = config
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None

    def startup(self) -> None:
        """Initialize the database connection."""

        try:
            logger.info(
                f"Attempting to connect to MySQL at: {self.config.database_url.split('@')[1] if '@' in self.config.database_url else 'localhost'}"
            )

            self.engine = create_engine(
                self.config.database_url,
                echo=self.config.echo_sql,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_pre_ping=True,  # Enable connection health checks to prevent stale connections
            )

            self.session_factory = sessionmaker(bind=self.engine)

            # Test the connection
            assert self.engine is not None, "Failed to create database engine"
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                logger.info("Database connection established successfully")

            # Check which tables exist before creating
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()

            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)

            # Check if any new tables were created
            current_tables = set(inspector.get_table_names())
            new_tables = current_tables - set(existing_tables)

            if new_tables:
                logger.info(f"Created new tables: {', '.join(new_tables)}")
            else:
                logger.info("All tables already exist, no new tables created")

            logger.info("MySQL database startup completed successfully")
            assert self.engine is not None
            logger.info(f"Database: {self.engine.url.database}")
            logger.info(f"Total tables: {', '.join(current_tables)}")
            logger.info("Database connection established and tables are ready")

        except Exception as e:
            logger.error(f"Error during MySQL database startup: {str(e)}")
            raise

    def teardown(self) -> None:
        """Close the database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("MySQL database connection closed successfully")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session."""
        if not self.session_factory:
            raise RuntimeError("Database session factory is not initialized")

        session = self.session_factory()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
