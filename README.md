# Project Name

> A short one-line description of what your project does.

A web application that combines an **HTML/CSS frontend**, a **Flask (Python) backend**, and **n8n** for workflow automation.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)
- [n8n Workflow Setup](#n8n-workflow-setup)
- [API Endpoints](#api-endpoints)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Describe the purpose of your project here:

- What problem does it solve?
- Who is it for?
- What are the main features?

**Key features**

- Simple and responsive frontend built with HTML and CSS
- REST API built with Flask
- Automated workflows powered by n8n (webhooks, notifications, data processing, etc.)

---

## Architecture

```
┌────────────┐   HTTP    ┌──────────────┐  Webhook  ┌──────────┐
│  Frontend  │ ────────► │ Flask Backend│ ────────► │   n8n    │
│ (HTML/CSS) │ ◄──────── │   (Python)   │ ◄──────── │ Workflow │
└────────────┘   JSON    └──────────────┘  Response └──────────┘
                                                        │
                                                        ▼
                                          External services (email,
                                          Google Sheets, Telegram, DB...)
```

1. The user interacts with the **frontend**.
2. The frontend sends requests to the **Flask backend**.
3. Flask processes the request and triggers an **n8n workflow** through a webhook.
4. n8n runs the automation and returns a result (or performs actions in external services).

---

## Tech Stack

| Layer      | Technology                 |
| ---------- | -------------------------- |
| Frontend   | HTML5, CSS3 (JavaScript optional) |
| Backend    | Python 3.10+, Flask        |
| Automation | n8n                        |
| Other      | Flask-CORS, python-dotenv, requests |

---

## Project Structure

```
project-root/
├── backend/
│   ├── app.py               # Flask application entry point
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment variables (not committed)
│   └── routes/              # (optional) API routes
├── frontend/
│   ├── index.html           # Main page
│   ├── css/
│   │   └── style.css        # Styles
│   └── js/
│       └── script.js        # (optional) Frontend logic
├── n8n/
│   └── workflow.json        # Exported n8n workflow
├── .env.example             # Example environment variables
├── .gitignore
└── README.md
```

> Adjust this tree to match your actual folder layout.

---

## Prerequisites

Make sure you have installed:

- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/) (required for running n8n via npm)
- [Git](https://git-scm.com/)
- (Optional) [Docker](https://www.docker.com/) to run n8n in a container

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. Set up the backend (Flask)

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Example `requirements.txt`:

```
Flask
flask-cors
python-dotenv
requests
```

### 3. Set up n8n

**Option A – npm**

```bash
npm install n8n -g
```

**Option B – Docker**

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n
```

---

## Configuration

Copy the example environment file and edit it:

```bash
cp .env.example backend/.env
```

Example `.env`:

```env
# Flask
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5000

# n8n
N8N_WEBHOOK_URL=http://localhost:5678/webhook/your-webhook-path
N8N_API_KEY=your_api_key_if_needed
```

> ⚠️ Never commit your real `.env` file. Add it to `.gitignore`.

---

## Running the Project

Open three terminals (or run the parts you need).

**1. Start n8n**

```bash
n8n start
```

n8n will be available at: <http://localhost:5678>

**2. Start the Flask backend**

```bash
cd backend
python app.py
```

The API will run at: <http://localhost:5000>

**3. Open the frontend**

Open `frontend/index.html` in your browser, or serve it locally:

```bash
cd frontend
python -m http.server 8000
```

Then visit: <http://localhost:8000>

---

## n8n Workflow Setup

1. Open n8n at <http://localhost:5678>.
2. Go to **Workflows → Import from file** and select `n8n/workflow.json`.
3. Open the **Webhook** node and copy the **Production URL**.
4. Paste it into `N8N_WEBHOOK_URL` in your `.env` file.
5. Configure credentials for any external services used (email, Google Sheets, Telegram, database, etc.).
6. **Activate** the workflow using the toggle in the top-right corner.

> Use the **Test URL** while developing and the **Production URL** once the workflow is active.

---

## API Endpoints

| Method | Endpoint       | Description                          |
| ------ | -------------- | ------------------------------------ |
| GET    | `/`            | Health check                         |
| POST   | `/api/submit`  | Receives data and triggers n8n       |
| GET    | `/api/status`  | Returns the status of the service    |

**Example request**

```bash
curl -X POST http://localhost:5000/api/submit \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com"}'
```

**Example response**

```json
{
  "success": true,
  "message": "Workflow triggered successfully"
}
```

---

## Usage

1. Open the frontend in your browser.
2. Fill in the form / interact with the page.
3. The frontend sends the data to the Flask API.
4. Flask forwards it to n8n, which runs the automation.
5. The result is displayed to the user.

*(Add screenshots here)*

```
![Screenshot](docs/screenshot.png)
```

---

## Troubleshooting

| Problem | Possible solution |
| ------- | ----------------- |
| **CORS error** in the browser | Make sure `flask-cors` is installed and enabled: `CORS(app)` |
| **404 on webhook** | Check that the n8n workflow is **active** and the URL/path is correct |
| **Connection refused** | Verify that Flask (port 5000) and n8n (port 5678) are running |
| **Module not found** | Activate the virtual environment and run `pip install -r requirements.txt` |

---

## Contributing

1. Fork the project
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m "Add amazing feature"`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Author

**Your Name** – [GitHub](https://github.com/your-username) · [LinkedIn](https://linkedin.com/in/your-profile)