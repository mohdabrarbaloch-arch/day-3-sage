# API Reference

Base path: `/api`

## Auth

### `POST /api/auth/signup`
Create an account. Body: `{ email, password (8-128), full_name? }`. Returns `201` with `{ access_token, token_type, user }`. `409` if email exists.

### `POST /api/auth/login`
Log in. Body: `{ email, password }`. Returns `200` with `{ access_token, token_type, user }`. `401` on bad credentials.

## Documents

All document routes require `Authorization: Bearer <token>`.

### `POST /api/documents`
Multipart upload with field `file`. Returns `201` with the document. `400` on bad extension, `413` on size, `422` on unreadable/empty PDF.

### `GET /api/documents`
List the current user's documents.

### `GET /api/documents/{id}`
Get a document including its full content. `404` if not owned.

### `DELETE /api/documents/{id}`
Delete a document. Returns `204`.

## Conversations

### `POST /api/conversations/ask`
Body: `{ question, document_id? | conversation_id? }`. Returns `{ conversation_id, question, answer, citations, grounded, blocked, block_reason }`.

### `GET /api/conversations`
List the user's conversations.

### `GET /api/conversations/{id}`
Get a conversation with its messages.

## Summarize

### `POST /api/summarize`
Body: `{ document_id, ratio? (0.1-0.9, default 0.3), max_sentences? (1-50, default 8) }`. Returns `{ document_id, summary, sentence_count, compression_ratio, grounded }`.

## Meta

### `GET /api/health`
No auth. Returns `{ status, app, version, environment }`.
