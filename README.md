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
