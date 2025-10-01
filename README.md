## Student Registration CRM (Malaysia)

Prerequisites:
- Python 3.13
- PostgreSQL 14+

Setup:
1. Copy env and edit:
   ```bash
   cp .env.example .env
   ```
2. Ensure a database exists and `DATABASE_URL` points to it.
3. (If venv unavailable) install requirements with override:
   ```bash
   python3 -m pip install --break-system-packages -r requirements.txt
   ```
   Preferably, create a venv if allowed.
4. Initialize DB:
   ```bash
   flask --app run.py db init
   flask --app run.py db migrate -m "init"
   flask --app run.py db upgrade
   ```
5. Seed super admin:
   ```bash
   flask --app run.py seed-admin --email admin@example.com --password admin123
   ```
6. Run app:
   ```bash
   python3 run.py
   ```

Key endpoints:
- `GET /api/health` health check
- `POST /api/auth/login` (HttpOnly cookies)
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `GET/POST /api/students`
- `GET /api/dashboard/kpis`

Security:
- JWT in HttpOnly cookies, CSRF protected
- AES-256-GCM encryption at rest for document blobs via `CryptoManager`

Notes:
- For local development without S3, files are stored under `STORAGE_DIR`.
# MyFitnessPal with CNN and OCR

This project is a fitness tracking application that leverages Convolutional Neural Networks (CNN) and Optical Character Recognition (OCR) to analyze and process fitness-related data. Built with FastAPI, it provides a robust backend for handling user data, image processing, and machine learning tasks.

## Features
- **OCR Integration**: Extract text from images using `pytesseract` and `pyzbar`.
- **Image Processing**: Analyze fitness-related images using OpenCV and `imagehash`.
- **Machine Learning**: Utilize PyTorch for CNN-based tasks.
- **Secure Authentication**: Implement JWT-based authentication with `python-jose` and `passlib`.
- **RESTful API**: Built with FastAPI for high performance and scalability.

## Requirements
- Python 3.10 or higher
- Virtual environment (recommended)
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd fitpal_plus_ai_ultra
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r fitpal_plus_ai_ultra/backend/requirements.txt
   ```

## Running the Application

### Locally
1. Navigate to the backend directory:
   ```bash
   cd fitpal_plus_ai_ultra/backend
   ```

2. Start the application:
   ```bash
   uvicorn main:app --host=0.0.0.0 --port=8000
   ```

3. Access the API at `http://127.0.0.1:8000`.

### On Netlify
1. Ensure the `netlify.toml` file is configured correctly.
2. Deploy the project to Netlify.

### On Heroku (Optional)
1. Ensure the `Procfile` is configured correctly.
2. Deploy the project to Heroku using Git.

## Project Structure
```
fitpal_plus_ai_ultra/
├── fitpal_plus_ai_ultra/
│   ├── backend/
│   │   ├── main.py  # FastAPI entry point
│   │   ├── models/  # Database models
│   │   ├── routes/  # API routes
│   │   ├── utils/   # Utility functions
│   │   ├── requirements.txt  # Dependencies
│   │   ├── Procfile  # Heroku deployment file
│   └── ...
├── netlify.toml  # Netlify configuration
└── README.md  # Project documentation
```

## Dependencies
Key dependencies include:
- `fastapi`: Web framework for building APIs.
- `uvicorn`: ASGI server for running FastAPI.
- `pytesseract`, `pyzbar`: OCR libraries.
- `opencv-python-headless`: Image processing.
- `torch`, `torchvision`: Machine learning with PyTorch.
- `gunicorn`: Production server.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.
