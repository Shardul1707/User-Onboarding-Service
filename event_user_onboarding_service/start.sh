cd /Users/shardul.powale/Desktop/event_user_onboarding_service
uvicorn app.main:app --host 0.0.0.0 --port 5000

#To start the consumer
cd /Users/shardul.powale/Desktop/event_user_onboarding_service
python -m app.consumers.user_consumer