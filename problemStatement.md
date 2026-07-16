# Problem Statement — MCP Server for Gmail & Google Docs

## Overview

Build a **generic, reusable MCP (Model Context Protocol) server** that exposes two core capabilities as tools any AI agent can call:

1. **Send / Draft emails via Gmail**
2. **Append content to a Google Doc**

The server must conform to the MCP specification so that it is **agent-agnostic**—any AI agent (Claude, Gemini, custom pipelines, etc.) that speaks MCP can discover and invoke these tools without writing bespoke Google API integration code.

---

## Motivation

Teams today want AI agents that can **act**, not just answer. Two of the most common "last-mile" actions are:

- **Emailing a stakeholder** (e.g., a weekly digest, an alert, a draft for human review).
- **Writing to a shared document** (e.g., appending a report section, logging results, updating a living doc).

Wiring up Google OAuth, REST clients, and token refresh for every new agent is repetitive and error-prone. An MCP server centralises this plumbing and lets agents focus on reasoning while the server handles auth and delivery.

### Concrete Use-Case: Weekly App-Review Pulse

A practical scenario that exercises both tools end-to-end:

| Step | Agent Action | MCP Tool Used |
|------|-------------|---------------|
| 1 | Cluster recent App Store / Play Store reviews into ≤ 5 themes | *(agent-internal)* |
| 2 | Generate a one-page weekly pulse (top 3 themes, 3 user quotes, 3 action ideas) | *(agent-internal)* |
| 3 | Append the pulse to a shared Google Doc | `google_docs.append_content` |
| 4 | Draft / send an email containing or linking to the pulse | `gmail.send_email` |

---

## Core Functionalities

### 1. Gmail — Send / Draft Email

| Capability | Description |
|-----------|-------------|
| **Send Email** | Compose and send an email to one or more recipients with subject, body (plain text and/or HTML), and optional attachments. |
| **Draft Email** | Create a draft in the authenticated user's Gmail account for manual review before sending. |
| **Reply / Forward** *(stretch)* | Reply to or forward an existing thread. |

**Tool Interface (example)**

```jsonc
{
  "name": "gmail.send_email",
  "description": "Send an email via the authenticated Gmail account.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "to":      { "type": "array", "items": { "type": "string" }, "description": "Recipient email addresses" },
      "cc":      { "type": "array", "items": { "type": "string" }, "description": "CC recipients (optional)" },
      "bcc":     { "type": "array", "items": { "type": "string" }, "description": "BCC recipients (optional)" },
      "subject": { "type": "string" },
      "body":    { "type": "string", "description": "Email body (plain text or HTML)" },
      "is_draft": { "type": "boolean", "default": false, "description": "If true, save as draft instead of sending" }
    },
    "required": ["to", "subject", "body"]
  }
}
```

### 2. Google Docs — Append Content

| Capability | Description |
|-----------|-------------|
| **Append Content** | Append text (plain or formatted) to an existing Google Doc identified by its document ID. |
| **Create & Append** *(stretch)* | Create a new Google Doc if one doesn't exist, then append content. |

**Tool Interface (example)**

```jsonc
{
  "name": "google_docs.append_content",
  "description": "Append content to an existing Google Doc.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "document_id": { "type": "string", "description": "Google Doc ID to append to" },
      "content":     { "type": "string", "description": "Content to append (Markdown or plain text)" },
      "format":      { "type": "string", "enum": ["plain", "markdown"], "default": "plain" }
    },
    "required": ["document_id", "content"]
  }
}
```

---

## Architecture Principles

| Principle | Detail |
|-----------|--------|
| **MCP-First** | All capabilities are exposed as MCP tools — no direct Google REST calls from the agent. |
| **Agent-Agnostic** | The server is a standalone process; any MCP-compatible client can connect (stdio, SSE, HTTP). |
| **Single Auth Layer** | Google OAuth 2.0 credentials are managed once inside the MCP server; agents never handle tokens. |
| **Extensible** | Adding a new Google Workspace tool (Sheets, Calendar, Drive) should follow the same pattern. |
| **Secure** | Credentials stored securely (env vars / secret manager). No PII leakage in logs. |

---

## Who This Helps

| Audience | Why |
|----------|-----|
| **AI Agent Developers** | Plug-and-play Gmail and Docs integration without OAuth boilerplate. |
| **Product / Growth Teams** | Automated delivery of insights (e.g., weekly pulse) to Docs and email. |
| **Support Teams** | Agents can draft follow-up emails aligned with user feedback. |
| **Leadership** | One-page health checks delivered to their inbox and a shared doc, zero manual effort. |

---

## Key Constraints

| Constraint | Detail |
|-----------|--------|
| **Privacy** | No PII (usernames, device IDs, etc.) in any artifact or log. |
| **Scoping** | Gmail scopes limited to `send` and `compose`; Docs scopes limited to `documents` read/write. Use least-privilege. |
| **Rate Limits** | Respect Google API quotas; implement back-off and retry. |
| **Transport** | Support at least **stdio** transport for local dev; optionally SSE / HTTP for remote deployment. |
| **Language** | Python or TypeScript (align with team preference). |

---

## Deliverables

1. **MCP Server** — A working server exposing `gmail.send_email` (with draft mode) and `google_docs.append_content` as MCP tools.
2. **Authentication Setup** — Scripts or documentation for configuring Google OAuth 2.0 credentials.
3. **README** — Setup guide, configuration reference, and usage examples.
4. **Demo / Integration Test** — End-to-end test that:
   - Appends a sample note to a Google Doc.
   - Sends (or drafts) an email containing that note.

---

## Success Criteria

- [ ] An external AI agent can discover the MCP server's tools via the MCP handshake.
- [ ] Agent can send an email through `gmail.send_email` and the recipient receives it.
- [ ] Agent can create a draft via the same tool with `is_draft: true`.
- [ ] Agent can append content to an existing Google Doc via `google_docs.append_content`.
- [ ] No Google API credentials are exposed to the calling agent.
- [ ] The server handles invalid inputs gracefully with meaningful MCP error responses.
