# AI-Powered Document Insight Tool

## Project Overview

This project is an AI-powered document insight tool designed to allow users to upload PDF documents—primarily resumes—and receive concise summaries or key insights. The application includes a backend service for document processing and AI integration, paired with a responsive frontend for user interaction. A key feature is the maintenance of a historical record of uploaded documents and their generated insights.

---

## Features

- Upload PDF files (resumes).
- Extract and summarize document content using an external AI service (Sarvam AI recommended).
- Graceful fallback to top five most frequent words when AI summarization is unavailable.
- Maintain and display a history of previously processed documents and their insights.
- Responsive frontend web interface for seamless user experience.

---

## Technical Stack

- **Backend:** Python FastAPI web framework.
- **AI Integration:** Sarvam AI for document summarization (free indigenous AI platform).
- **Frontend:** Web UI for file upload, analysis display, and history.
- **PDF Processing:** PyPDF2 for text extraction.
- **Data Persistence:** In-memory dictionary for history; can be enhanced for persistence across sessions.
- **HTTP Client:** `httpx` for asynchronous AI API calls.

---

## API Endpoints

### 1. `/upload-resume` (POST)

- Accepts PDF file uploads.
- Extracts text content from PDF.
- Sends text to Sarvam AI for summary generation.
- Returns summary or fallback insights.
- Updates the upload history with insights.

### 2. `/insights` (GET)

- Retrieves the history of all uploaded documents and their insights.
- Supports identification/query parameters for specific insights retrieval (to be implemented/enhanced).

---