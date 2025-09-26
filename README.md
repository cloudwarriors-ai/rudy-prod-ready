# 🚀 Microsoft Teams SDK FastAPI

A comprehensive FastAPI application for managing Microsoft Teams infrastructure including users, teams, call queues, and Auto Attendants (IVR systems) with Azure Communication Services integration.

## 📁 Project Structure

```
teams-sdk/
├── 📄 app.py                    # Main FastAPI application
├── 📄 .env                      # Environment variables
├── 📄 connect.ps1               # PowerShell connection script
├── 📄 README.md                 # This file
│
├── 📁 docs/                     # 📚 Documentation
│   ├── teamsapi.md              # Complete API documentation
│   ├── azureconfig.md           # Azure configuration guide
│   ├── CALL_QUEUE_ENDPOINTS.md  # Call queue integration guide
│   ├── create_documentation.md  # Documentation creation guide
│   ├── research.md              # Research and references
│   ├── emergency-addresses.md   # 🚨 Emergency Address Configuration
│   └── auto-attendant/          # 🎯 Auto Attendant Documentation
│       ├── README.md            # AA documentation index & quick start
│       ├── auto-attendant-build-process.md  # Complete build guide + API reference
│       ├── auto-attendant-fields.md         # Field definitions & parameters
│       ├── aa-analysis.md                   # Technical analysis & insights
│       ├── BUSINESS_HOURS_SOLUTION.md       # Business hours implementation
│       ├── BUSINESS_HOURS_COMPLETE.md       # Business hours status
│       ├── test_aa_params.json              # Sample parameters & schemas
│       └── scripts/                         # PowerShell scripts & examples
│           ├── README.md                    # Script documentation & patterns
│           ├── test-autoattendant-creation.ps1
│           └── test-business-hours-schedules.ps1
│
├── 📁 auth-keys/                # 🔐 Authentication certificates
│   ├── teamsfed.pfx             # PKCS#12 certificate bundle
│   ├── teamsfed.crt             # Public certificate
│   └── teamsfed.key             # Private key
│
├── 📁 python-testing/           # 🧪 Python test scripts
│   ├── test_*.py                # Various API test scripts
│   └── debug_*.py               # Debug and testing utilities
│
├── 📁 debug/                    # 🔧 Debug infrastructure  
│   ├── powershell/              # PowerShell debug scripts
│   ├── api/                     # API testing scripts
│   └── logs/                    # Debug operation logs
│
├── 📁 examples/                 # 📖 Usage examples
│   └── simple_test.sh           # Simple test script example
│
├── 📁 logs/                     # 📋 Application logs
│   └── *.log                    # Various operation logs
│
├── 📁 openapi-spec/             # 📋 API specifications
│   ├── openapi.json             # OpenAPI/Swagger specification
│   └── teams_api.postman_collection.json  # Postman collection
│
├── 📁 debug/                    # 🐛 PowerShell debugging scripts
│   └── *.ps1                    # Various debug PowerShell scripts
│
├── 📁 working-samples/          # ✅ Working example scripts
│   └── create-user/             # User creation examples
│
└── 📁 venv/                     # 🐍 Python virtual environment
```

## 🚀 Quick Start

### 1. Start the API Server
```bash
# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
uvicorn app:app --host 127.0.0.1 --port 9000
```

### 2. Test Authentication
```bash
curl -X POST "http://localhost:9000/auth/connect"
```

### 3. Access API Documentation
Visit: `http://localhost:9000/docs` for interactive Swagger UI

## 🎯 Key Features

### 👥 **User Management**
- Create Azure AD users with full profiles
- Session-based and direct creation methods
- Password policy enforcement

### 🏢 **Team Management**  
- Create Microsoft Teams
- Add members to teams
- Configure team settings

### 📞 **Call Queue Management**
- Create and configure call queues
- Add agents to queues
- Multiple routing methods (Serial, RoundRobin, etc.)

### 📱 **Auto Attendant (IVR)**
- Create interactive voice response systems
- Multi-level menu navigation
- Route calls to appropriate queues/users

### ☁️ **Azure Communication Services Integration**
- Object ID formatting for calling (`28:orgid:{guid}`)
- Direct integration with ACS Calling SDK
- Complete call center functionality

## 📖 Documentation

- **📘 Complete API Guide**: [`docs/teamsapi.md`](docs/teamsapi.md)
- **🔧 Azure Setup Guide**: [`docs/azureconfig.md`](docs/azureconfig.md)  
- **📞 Call Queue Guide**: [`docs/CALL_QUEUE_ENDPOINTS.md`](docs/CALL_QUEUE_ENDPOINTS.md)
- **🧪 Testing Guide**: [`docs/unified-test-guide.md`](docs/unified-test-guide.md)
- **📊 Testing Status**: [`docs/testing-status.md`](docs/testing-status.md)

## 🔐 Authentication

Uses certificate-based authentication with Microsoft Graph and Teams PowerShell modules:
- **Certificate files**: Located in `auth-keys/`
- **Configuration**: See `connect.ps1` for connection setup
- **Permissions**: Requires Teams administrator and Graph API permissions

## 🧪 Testing

### Unified Call Center Test Script

Test the complete call center workflow with a single command:

```bash
# Recommended test (with unique usernames)
TIMESTAMP=$(date +%s)
python3 test_unified_call_center.py \
    --user-name "Test User $TIMESTAMP" \
    --user-email "testuser${TIMESTAMP}@cloudwarriors.onmicrosoft.com" \
    --queue-name "Test Queue $TIMESTAMP" \
    --aa-name "Test IVR $TIMESTAMP"

# Quick test using example script
./examples/simple_test.sh
```

**What it tests:**
1. ✅ **User Creation** - Creates new user with proper authentication  
2. ✅ **Call Queue Creation** - Creates call queue with RoundRobin routing
3. ✅ **Agent Assignment** - Successfully adds user as agent to the queue
4. ⚠️ **Auto Attendant Creation** - Tests IVR creation (requires resource accounts)
5. ✅ **End-to-End Verification** - Validates complete setup with detailed reporting

**✅ Core call center functionality (User + Queue + Agent) works reliably!**

### Test Organization

- **`test_unified_call_center.py`**: Complete workflow testing
- **`python-testing/`**: Individual API tests and utilities
- **`debug/`**: PowerShell debugging and investigation scripts
- **`examples/`**: Usage examples and simple test cases
- **`docs/unified-test-guide.md`**: Detailed testing documentation

## 🌟 Example Call Center Flow

```
Azure Communication Services → Auto Attendant (IVR) → Call Queues → Agents
                             ↓
                        "Welcome to Acme Corp!"
                        "Press 1 for Sales, Press 2 for Support"
                             ↓
                    Routes to appropriate queue
                             ↓
                    Distributes to available agents
```

## 🤝 Contributing

1. Keep the folder structure organized
2. Update documentation when adding features  
3. Test new functionality before committing
4. Follow the established naming conventions

---

**Built with ❤️ for enterprise Microsoft Teams integration**