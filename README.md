# Distributed LiveChat System

A modern, distributed real-time chat application built with Flask, Socket.IO, and PostgreSQL. The system is refactored into microservices for better scalability and maintainability.

## Architecture

The application is split into two main microservices:

1.  **Auth Service** (`auth_service.py`): Handles user registration, login, and session management.
    *   **Port**: 5000
2.  **Chat Service** (`chat_service.py`): Handles real-time messaging, chat rooms, and Socket.IO events.
    *   **Port**: 5001

Both services share a PostgreSQL database and use a common utility module for database connections and JWT token handling.

## Prerequisites

*   **Python 3.8+**
*   **PostgreSQL** (or Docker to run it in a container)
*   **pip** (Python package manager)

## Installation

1.  **Clone the repository** (if you haven't already).

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(If `requirements.txt` is missing, install manually: `pip install flask flask-socketio psycopg2-binary python-dotenv`)*

## Database Setup

We recommend using Docker to run the PostgreSQL database to avoid local environment issues.

1.  **Start Docker** (e.g., using Colima on macOS):
    ```bash
    colima start
    ```

2.  **Run PostgreSQL Container**:
    ```bash
    docker run --name postgres_alpine -e POSTGRES_PASSWORD=postgres -d -p 5432:5432 postgres:alpine
    ```

3.  **Initialize the Database**:
    Run the initialization script to create the necessary tables (`users`, `room`, `messages`, etc.).
    ```bash
    # Ensure you are in the project root
    export DB_HOST=localhost DB_NAME=postgres DB_USER=postgres DB_PASS=postgres FLASK_SECRET=dev_secret
    python3 init_db.py
    ```

## Configuration

1.  **Create a `.env` file** in the project root:
    ```bash
    cp .env.example .env
    ```

2.  **Edit `.env`** (if needed) to match your database credentials:
    ```ini
    DB_HOST=localhost
    DB_NAME=postgres
    DB_USER=postgres
    DB_PASS=postgres
    FLASK_SECRET=your_secret_key
    ```

## Running the Application

You need to run both services simultaneously. Open two terminal windows:

**Terminal 1: Auth Service**
```bash
export DB_HOST=localhost DB_NAME=postgres DB_USER=postgres DB_PASS=postgres FLASK_SECRET=dev_secret
python3 services/auth_service.py
```

**Terminal 2: Chat Service**
```bash
export DB_HOST=localhost DB_NAME=postgres DB_USER=postgres DB_PASS=postgres FLASK_SECRET=dev_secret
python3 services/chat_service.py
```

*Note: You can also use the values from your `.env` file if you load them, but exporting them directly ensures they are picked up.*

## Stopping the Database

To stop the PostgreSQL Docker container:
```bash
docker stop postgres_alpine
```
To remove the container (if you want to start fresh later):
```bash
docker rm postgres_alpine
```

## Usage

1.  Open your browser and go to: **`http://127.0.0.1:5000`**
2.  **Register** a new account.
3.  **Login** with your credentials.
4.  You will be automatically redirected to the **Chat Service** (`http://127.0.0.1:5001`).
5.  **Create a Room** or **Join** an existing one using a code.
6.  Start chatting!

## Troubleshooting

### macOS Port 5000 Conflict (AirTunes)
If you encounter a **403 Forbidden** error during logout or redirects, it is likely because port 5000 is occupied by AirTunes (AirPlay Receiver) on `localhost`.

*   **Solution**: The application is configured to use `127.0.0.1` instead of `localhost` for service-to-service communication. **Always access the app via `http://127.0.0.1:5000`**, not `localhost`.

### Database Connection Errors
If you see `psycopg2.OperationalError`, ensure your Docker container is running:
```bash
docker ps
```
If it's not running, restart it:
```bash
docker start postgres_alpine
```