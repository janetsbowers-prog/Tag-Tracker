# Tag Tracker 🏷️

A mobile-friendly web application for scanning and tracking clothing tags with automatic return date calculation.

## Features

- 📸 Mobile camera interface for easy tag scanning
- 🤖 AI-powered text extraction from tag images
- 📅 Automatic return date calculation (30 days from scan)
- 💾 Database storage of all scanned tags
- 📱 Fully responsive design optimized for phone use
- 🔍 Searchable tracker sorted by return date
- 📊 CSV export functionality

## Tech Stack

- **Backend**: Flask (Python)
- **AI Vision**: Anthropic Claude API
- **Frontend**: HTML5, CSS, JavaScript
- **Database**: PostgreSQL (Heroku) / SQLite (local)
- **Deployment**: Heroku

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variable: `ANTHROPIC_API_KEY`
4. Run locally: `python app.py`

## Deployment

Configured for Heroku deployment with Procfile and requirements.txt included.

## Usage

1. Open the app on your phone
2. Grant camera permissions
3. Take a photo of a clothing tag
4. AI automatically extracts style #, description, and PO #
5. Review/edit extracted data
6. Scan date auto-fills (editable)
7. Return date auto-calculates as scan date + 30 days
8. Save to tracker

---

Built with ❤️ for FAM Brands
