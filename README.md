# Google Workspace MCP Server

A generic, agent-agnostic **MCP (Model Context Protocol) server** that exposes Gmail and Google Docs as tools any AI agent can call.

| Tool | Description |
|------|-------------|
| `gmail_send_email` | Send or draft emails via Gmail |
| `google_docs_append` | Append plain text or markdown to a Google Doc |

Built with [FastMCP](https://github.com/modelcontextprotocol/python-sdk) — any MCP-compatible client (Claude Desktop, Cursor, custom agents) can discover and invoke these tools automatically.

---

## Prerequisites

- **Python 3.10+**
- **Google Cloud project** with Gmail API and Google Docs API enabled
- **OAuth 2.0 Client ID** (Desktop application type)

---

## Google Cloud Setup

If you don't have a Google Cloud project yet, follow these steps:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. **Enable APIs:**
   - Navigate to **APIs & Services → Library**
   - Search for and enable **Gmail API**
   - Search for and enable **Google Docs API**
4. **Create OAuth Credentials:**
   - Go to **APIs & Services → Credentials**
   - Click **Create Credentials → OAuth 2.0 Client ID**
   - Application type: **Desktop app**
   - Download the JSON file and save it as `credentials.json` in the project root
5. **Configure OAuth Consent Screen:**
   - Go to **APIs & Services → OAuth consent screen**
   - Choose **External** (or Internal for Workspace)
   - Add your email as a test user
   - Add scopes:
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/gmail.compose`
     - `https://www.googleapis.com/auth/documents`

---

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd "MCP Server"

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

---

## Configuration

Copy the example environment file and adjust if needed:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_CREDENTIALS_PATH` | `./credentials.json` | Path to OAuth client ID JSON |
| `GOOGLE_TOKEN_PATH` | `./token.json` | Path where the auth token is saved |

---

## First Run & Authentication

```bash
python server.py
```

On the first run, your browser will open for Google OAuth consent. Grant the requested permissions. A `token.json` file will be created automatically — subsequent runs will use this token (and refresh it when expired).

> **Note:** When using stdio transport, the server communicates via stdin/stdout. The OAuth browser flow happens once; after that, the server runs headless.

---

## Connecting to AI Agents

### Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "python",
      "args": ["C:/full/path/to/MCP Server/server.py"]
    }
  }
}
```

Restart Claude Desktop — the tools will appear in the tool picker.

### Cursor

Add to your Cursor MCP config (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "python",
      "args": ["C:/full/path/to/MCP Server/server.py"]
    }
  }
}
```

### MCP Inspector (Testing)

```bash
mcp dev server.py
```

This opens a web UI where you can test both tools interactively.

---

## Tool Reference

### `gmail_send_email`

Send an email or save it as a draft.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `to` | `list[str]` | ✅ | Recipient email addresses |
| `subject` | `str` | ✅ | Email subject line |
| `body` | `str` | ✅ | Email body (plain text or HTML) |
| `cc` | `list[str]` | ❌ | CC recipients |
| `bcc` | `list[str]` | ❌ | BCC recipients |
| `is_draft` | `bool` | ❌ | Save as draft instead of sending (default: `false`) |

**Example response:**
```json
{
  "status": "sent",
  "message_id": "18a1b2c3d4e5f6g7",
  "thread_id": "18a1b2c3d4e5f6g7"
}
```

### `google_docs_append`

Append content to an existing Google Doc.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `document_id` | `str` | ✅ | Google Doc ID (from URL) |
| `content` | `str` | ✅ | Text to append |
| `format` | `str` | ❌ | `"plain"` (default) or `"markdown"` |

**Example response:**
```json
{
  "status": "appended",
  "document_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUii3Op3Rp6mLbKd",
  "characters_added": 142
}
```

**Markdown support:** When `format="markdown"`, the tool converts:
- `# Heading` → Google Docs Heading 1–6
- `**bold**` → Bold text
- `*italic*` → Italic text

---

## Development

### Running Unit Tests

```bash
# All unit tests (no credentials needed)
pytest tests/test_gmail_tool.py tests/test_docs_tool.py -v
```

### Running Integration Tests

Requires real credentials and environment variables:

```bash
# Set test targets
set TEST_DOCUMENT_ID=your-google-doc-id
set TEST_EMAIL_RECIPIENT=your-email@example.com

# Run integration tests
pytest tests/test_integration.py -v -m integration
```

### Adding a New Tool

1. Create a new module in `tools/` (e.g., `tools/sheets_tool.py`)
2. Add any new scopes to `config/scopes.py`
3. Register the tool in `server.py` with `@mcp.tool()`
4. Add unit tests in `tests/`
5. Re-run `python server.py` or restart your MCP client

---

## Deploy to Railway

This server can be deployed to [Railway](https://railway.app) for remote access via SSE transport.

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: MCP server for Gmail & Google Docs"
git remote add origin https://github.com/<YOUR_USERNAME>/<REPO_NAME>.git
git branch -M main
git push -u origin main
```

### Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app) → sign in
2. **New Project** → **Deploy from GitHub Repo** → select your repo
3. Railway will auto-detect the `Procfile` and start deploying

### Step 3: Set Environment Variables

In Railway dashboard → your service → **Variables** tab:

| Variable | Value |
|----------|-------|
| `GOOGLE_TOKEN_JSON` | *Paste the entire contents of your local `token.json`* |
| `MCP_TRANSPORT` | `sse` |

> **Note:** Railway automatically sets `PORT`. The server detects this and switches to SSE transport.

### Step 4: Connect Your Agent

After deploy, Railway provides a public URL. Your SSE endpoint is:

```
https://your-app.railway.app/sse
```

**Claude Desktop** (remote SSE):
```json
{
  "mcpServers": {
    "google-workspace": {
      "url": "https://your-app.railway.app/sse"
    }
  }
}
```

---

## Project Structure

```
MCP Server/
├── server.py                  # MCP server entry point (FastMCP)
├── Procfile                   # Railway process definition
├── runtime.txt                # Python version for Railway
├── tools/
│   ├── gmail_tool.py          # Gmail send/draft logic
│   └── google_docs_tool.py    # Google Docs append logic
├── auth/
│   └── google_auth.py         # Shared OAuth 2.0 auth helper
├── config/
│   └── scopes.py              # Centralised Google API scopes
├── tests/
│   ├── test_gmail_tool.py     # Gmail unit tests
│   ├── test_docs_tool.py      # Docs unit tests
│   └── test_integration.py    # End-to-end integration tests
├── generate_token.py          # OAuth token generator utility
├── credentials.json           # OAuth client ID (gitignored)
├── token.json                 # Auto-generated token (gitignored)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Security

- **credentials.json** and **token.json** are gitignored — never commit them.
- For deployment, credentials are loaded from **environment variables** — no secrets in code.
- The server uses **least-privilege scopes** (send/compose for Gmail, documents for Docs).
- AI agents **never** see or handle Google credentials — the MCP server manages auth internally.
- No PII is logged.

---

## License

MIT

