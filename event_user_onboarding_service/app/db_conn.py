from sqlalchemy import create_engine, MetaData, orm
from sqlalchemy.ext.automap import automap_base
from contextlib import contextmanager
from dotenv import load_dotenv
import os
import ast
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path="app/configs/.env")

class Database:
    def __init__(self):
        self.engine = create_engine(os.getenv("DB_URL"), 
                                    pool_pre_ping=True, 
                                    pool_size=int(os.getenv("POOL_SIZE")), 
                                    max_overflow=int(os.getenv("MAX_OVERFLOW")), 
                                    echo=False)
        self.metadata = MetaData()
        self.metadata.reflect(self.engine,only=ast.literal_eval(os.getenv("TABLES")))
        self.Base = automap_base(metadata=self.metadata)
        self.Base.prepare()

        self._session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
            )
        )
        logger.info(f"Database Connection initialized with tables: {self.metadata.tables.keys()}")

    @contextmanager
    def get_db(self):
        db = self._session_factory()
        try:
            yield db
        except Exception as e:
            logger.error(f"Error getting database session: {e}")
            db.rollback()
            raise e
        finally:
            db.close()

    def get_table_class(self, table_name: str):
        return getattr(self.Base.classes, table_name)

    def db_connection_close(self):
        self.engine.dispose()
        logger.info("Database connection closed")
