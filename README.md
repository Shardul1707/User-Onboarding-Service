# User-Onboarding-Service
A scalable, event-driven micro-service for user registration and onboarding built with FastAPI, PostgreSQL, and RabbitMQ. This service handles user signup, validation, and asynchronous processing with robust error handling and retry mechanisms.

## 🚀 Features

- **RESTful API**: FastAPI-based endpoints for user registration and management
- **Asynchronous Processing**: RabbitMQ message queue for decoupled, scalable user onboarding
- **Database Integration**: PostgreSQL with SQLAlchemy ORM for reliable data persistence
- **Error Handling**: Comprehensive retry logic with exponential backoff
- **Dead Letter Queue (DLQ)**: Automatic handling of failed messages
- **Message TTL**: Time-to-live configuration for message expiration
- **Connection Resilience**: Auto-reconnection for database and message queue
- **Request Validation**: Pydantic models for data validation
- **Logging**: Comprehensive logging for monitoring and debugging

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.110.0
- **Database**: PostgreSQL with SQLAlchemy 1.4.35
- **Message Queue**: RabbitMQ with Pika 1.3.2
- **Server**: Uvicorn 0.17.6
- **Language**: Python 3.11+

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL 12+ (running and accessible)
- RabbitMQ 3.8+ (running and accessible)
- pip (Python package manager)

## 🏗️ Architecture

┌─────────────┐
│   FastAPI   │
│   Server    │
└──────┬──────┘
       │
       ├───► PostgreSQL (User Data)
       │
       └───► RabbitMQ (Message Queue)
                 │
                 └───► Consumer Worker
                          │
                          └───► Process & Store

## Components

API Layer: FastAPI endpoints handling HTTP requests
Business Logic: View functions for user operations
Data Layer: SQLAlchemy ORM for database operations
Message Queue: RabbitMQ for asynchronous task processing
Consumer: Background worker processing onboarding tasks


## 🔄 Message Flow

1. User Registration Request → FastAPI endpoint
2. Validation → Check if user already exists
3. Publish to Queue → Send user data to RabbitMQ
4. Consumer Processing → Background worker processes message
5. Database Storage → User data saved to PostgreSQL
6. Response → Return success/error to client

## 🛡️ Error Handling

1. Retry Logic: Exponential backoff for transient failures
2. Dead Letter Queue: Failed messages after max retries
3. Connection Resilience: Auto-reconnect for database and RabbitMQ
4. Graceful Degradation: Service continues even if one component fails

## 🏃 Running the Service

Start the API Server:

uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

The API will be available at: http://localhost:5000

Start the Consumer In a separate terminal:

python -m app.consumers.user_consumer
