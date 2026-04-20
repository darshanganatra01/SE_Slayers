# SE Slayers Project Documentation

## Product Overview
This repository contains the source code for the SE Slayers application, featuring a Flask backend, a Vue.js frontend, and a Celery-based background task processor integrated with Redis.

## Technical Architecture
The application is structured into two main components:
1.  **Backend**: A Flask application serving the REST API and managing background tasks via Celery.
2.  **Frontend**: A Vue.js application built with Vite and Tailwind CSS.
3.  **Infrastructure**: Redis is utilized as the message broker for Celery, managed within a Docker container.

## Prerequisites
Ensure the following software is installed on the host system:
*   Python 3.10 or higher
*   Node.js (Version 20 or higher)
*   Docker Desktop
*   Git

## Local Environment Setup

### 1. Database and Message Broker
Redis must be running to handle background tasks.
1.  Open Docker Desktop.
2.  Pull the Redis image if not present: `docker pull redis`.
3.  Run the Redis container: `docker run -d -p 6379:6379 --name se-redis redis`.

### 2. Backend Configuration
Navigate to the `backend` directory and perform the following steps:
1.  Create a virtual environment: `python -m venv venv`.
2.  Activate the virtual environment:
    *   Windows: `.\venv\Scripts\activate`
    *   Unix/macOS: `source venv/bin/activate`
3.  Install required dependencies: `pip install -r requirements.txt`.
4.  Configure the environment: Ensure a `.env` file exists with the necessary `DATABASE_URL` and `SECRET_KEY`.
5.  Start the Flask server:
    ```bash
    python run.py
    ```
    The API will be available at `http://localhost:5000`.

### 3. Background Task Runner (Celery)
Celery handles asynchronous tasks such as demand forecasting models.
1.  Open a new terminal in the `backend` directory.
2.  Activate the virtual environment.
3.  Execute the Celery worker:
    ```bash
    celery -A celery_app.celery_app worker --loglevel=info -P solo
    ```
    *Note: The `-P solo` flag is required for stability on Windows systems.*

### 4. Frontend Configuration
Navigate to the `frontend` directory and perform the following steps:
1.  Install Node dependencies: `npm install`.
2.  Launch the development server:
    ```bash
    npm run dev
    ```
    The application interface will be accessible at the URL provided in the terminal (typically `http://localhost:5173`).

## Project Structure Reference
*   `/backend`: API implementation, database models, and Celery tasks.
*   `/frontend`: Vue components, state management (Pinia), and styling.
*   `/tests`: Automated test suites for backend logic.

## Usage Instructions
*   Access the administrative dashboard by navigating to the frontend URL.
*   The default administrative credentials are provided in the internal configuration documentation.
*   API documentation can be viewed at `http://localhost:5000/api/docs` when the backend is running.
