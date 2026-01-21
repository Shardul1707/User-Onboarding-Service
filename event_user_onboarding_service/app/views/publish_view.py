from app.helpers.helper import get_rmq_instance, get_db_instance
from fastapi import HTTPException
from sqlalchemy.sql import func
from sqlalchemy import update
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def publish_to_rmq(data: dict):
    try:
        #PUBLISH TO RMQ
        rmq = get_rmq_instance()
        
        if not rmq.channel or rmq.channel.is_closed:
            rmq.connect()
        
        # Publish message (will auto-reconnect if connection is lost)
        rmq.publish_message('user_onboarding_queue', data)
        logger.info(f"Message published to RMQ: {data}")
    except Exception as e:
        logger.error(f"Error publishing to RMQ: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def user_exists(user_id: str):
    try:
        # Use global db instance from main, or create new one if not available
        database = get_db_instance()
        user = database.get_table_class("users")
        with database.get_db() as sess:
            q = sess.query(user).filter(func.lower(user.email) == user_id.lower()).first()
            if q:
                return {"status": True, "user_id": q.user_id, "verification": q.verification_state}
            else:
                return {"status": False, "user_id": None, "verification": None}
    except Exception as e:
        logger.error(f"Error checking if user exists: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def onboard_user(data: dict):
    try:
        user_data = user_exists(data["email"])
        if user_data["status"]:
            raise HTTPException(status_code=409, detail={"status": "SUCCESS", "message": "User already exists", "user_id": user_data["user_id"] , "verification": user_data["verification"]})
        
        user_id = str(uuid.uuid4())
        data["user_id"] = user_id
        data["verification"] = "PENDING"
        #PUBLISH TO RMQ
        publish_to_rmq(data)
        return {"status": "SUCCESS", "message": "User onboarded successfully", "user_id": user_id , "verification": "PENDING"}

    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_user_details(userid: str):
    try:
        database = get_db_instance()
        user = database.get_table_class("users")
        with database.get_db() as sess:
            q = sess.query(user).filter(func.lower(user.user_id) == userid.lower()).first()
            if q:
                return {"status": "SUCCESS", "message": "User details fetched successfully", "user_id": q.user_id, "email": q.email, "first_name": q.first_name, "last_name": q.last_name, "verification_state": q.verification_state, "created_on": q.created_on}
            else:
                raise HTTPException(status_code=404, detail={"status": "FAILURE", "message": "User not found", "user_id": None, "email": None, "first_name": None, "last_name": None, "verification_state": None, "created_on": None})

    except HTTPException as e:
        raise
            
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def update_user_details(userid: str):
    try:
        database = get_db_instance()
        user = database.get_table_class("users")
        with database.get_db() as sess:
            q = sess.query(user).filter(func.lower(user.user_id) == userid.lower()).first()
            if q:
                if q.verification_state == "VERIFIED":
                    return {"status": "SUCCESS", "message": "User already verified", "user_id": userid}
                upd = update(user).values({"verification_state": "VERIFIED"}).where(user.id == q.id)
                sess.execute(upd)
                sess.commit()
                logger.info(f"User {userid} verified successfully")
                return {"status": "SUCCESS", "message": "User verified successfully", "user_id": userid}
            else:
                raise HTTPException(status_code=404, detail={"status": "FAILURE", "message": "User not found", "user_id": userid})
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Error updating user details: {e}")
        raise HTTPException(status_code=500, detail=str(e))