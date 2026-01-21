from fastapi import APIRouter, HTTPException, status
from app.views.publish_view import onboard_user, get_user_details, update_user_details
from app.schema import UserRequest, UserResponse, UserDetailsResponse
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def publish(request: UserRequest):
    data = request.dict()
    logger.info(f"Request received: {data}")
    try:
        user_response = onboard_user(data)
        return user_response
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
def get_user(user_id: str):
    try:
        user_details = get_user_details(user_id)
        return user_details
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}", status_code=status.HTTP_200_OK)
def update_user(user_id: str):
    try:
        user_details = update_user_details(user_id)
        return user_details
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))