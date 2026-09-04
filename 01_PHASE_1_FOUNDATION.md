# Phase 1 — Foundation

## Objective

Build the stable local application foundation for Sovereign AI.

## Scope

### Web Application
Implement:
- Modern enterprise UI
- Sidebar
- Chat workspace
- Files
- Settings
- System status
- Responsive layout

### Backend
Separate:
- API routes
- Services
- Database
- AI abstraction
- Configuration
- Authentication
- Logging

### Authentication
Implement:
- First-run administrator creation
- Login/logout
- Protected routes
- Secure password storage
- Session/token handling

### Database

Initial entities:
- Users
- Conversations
- Messages
- Files
- Tasks
- Audit events

Use migrations.

### Local Model Abstraction

Create:

```text
ModelProvider
├── chat()
├── generate()
├── stream()
├── vision()
└── health_check()
```

Initially support a local backend such as Ollama, while keeping the interface provider-independent.

### Chat

Support:
- New conversation
- History
- Streaming
- Stop generation
- Model selection
- Persistence
- Markdown
- Code blocks

### File Management

Support:
- PDF
- DOCX
- XLSX
- PPTX
- TXT
- CSV
- Images

Phase 1 only requires secure storage and metadata.

### Docker

Provide:
- Dockerfile
- docker-compose.yml
- .env.example
- Persistent volumes

### Health

Display:
- Backend
- Database
- Model backend
- Storage

## Acceptance Test

A fresh deployment must allow:

```text
Docker Start
    ↓
Setup Admin
    ↓
Login
    ↓
Select Local Model
    ↓
Chat
    ↓
Upload File
```

No cloud API may be required.
