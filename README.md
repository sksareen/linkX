# LinkX

A minimalist link-sharing platform for X users with a clean, 4chan-inspired interface.

## Features
- X OAuth authentication
- Simple link management
- Clean, minimalist interface
- Share multiple types of links (demo videos, GitHub repos, web apps)
- Directory-style link organization

## Setup
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your X API credentials:
   ```
   X_API_KEY=your_api_key
   X_API_SECRET=your_api_secret
   X_CALLBACK_URL=http://localhost:5000/callback
   ```
5. Run the application:
   ```bash
   python app.py
   ```

## Tech Stack
- Backend: Flask (Python)
- Frontend: Vanilla JavaScript
- Database: SQLAlchemy with SQLite
- Authentication: X OAuth
