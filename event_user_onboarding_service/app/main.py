from fastapi import FastAPI, APIRouter, HTTPException
from app.endpoints.publish_endpoint import router as publish_router
from app.db_conn import Database
from app.rmq_adapter import RabbitMQHelper
from app.helpers.helper import retry
import logging


logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__)


router = APIRouter()

app = FastAPI(title = "User Onboarding Service",
              description = "User Onboarding Service",
              version = "1.0.0")


@app.on_event("startup")
async def startup_event():
    """Initialize Database and RabbitMQ with retry logic"""
    global db, rmq
    
    # Initialize Database
    try:
        db = retry(lambda: Database(), "Database initialization")
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database failed: {e}")
        db = None
    
    # Initialize RabbitMQ
    try:
        rmq = retry(lambda: RabbitMQHelper(), "RabbitMQ initialization")
        retry(lambda: rmq.connect(), "RabbitMQ connection")
        retry(lambda: rmq.setup_queue(), "RabbitMQ queue setup")
        logger.info("RabbitMQ initialized")
    except Exception as e:
        logger.error(f"RabbitMQ failed: {e}")
        rmq = None
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Close Database and RabbitMQ connections with retry logic"""
    global db, rmq
    
    if db:
        try:
            retry(lambda: db.db_connection_close(), "Database closure")
            logger.info("Database closed")
        except Exception as e:
            logger.error(f"Database closure failed: {e}")
    
    if rmq:
        try:
            retry(lambda: rmq.close(), "RabbitMQ closure")
            logger.info("RabbitMQ closed")
        except Exception as e:
            logger.error(f"RabbitMQ closure failed: {e}")
    
    logger.info("Application shutdown complete")

router.include_router(publish_router, tags = ["User Data Onboarding"])

app.include_router(router)