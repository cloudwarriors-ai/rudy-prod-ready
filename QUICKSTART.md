# Teams SDK Quickstart

## Step 1: Setup Environment
Update your `.env` file with your macOS password:
```bash
echo "CLI_PASSWORD=yourpassword" > .env
```

## Step 2: AI Agent Setup
Tell your AI agent to:
1. Read the `AGENTS.md` file
2. Follow the "Run These Steps First" section to install PowerShell and modules

## Step 3: Start Development
```bash
source venv/bin/activate
uvicorn app:app --host 127.0.0.1 --port 9000 --reload --log-level debug
```

Visit `http://localhost:9000/docs` for API documentation.