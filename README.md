# backlog-buddy
backlog cleaner for steam

## Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your Steam API key

# Run the server
python app.py
```

### Frontend Setup
```bash
cd frontend
# Open index.html in your browser, or use:
python -m http.server 8000
# Then visit http://localhost:8000
```

### Getting a Steam API Key
1. Go to https://steamcommunity.com/dev/apikey
2. Fill out the form (use http://localhost for domain)
3. Copy your key to backend/.env

### Finding Your Steam ID
1. Go to https://steamid.io/
2. Enter your Steam profile URL
3. Copy the steamID64 (17-digit number)

## Project Structure
- `/backend` - Flask API server
- `/frontend` - HTML/CSS/JS interface
- `/docs` - Documentation and notes

## API Endpoints
- `GET /health` - Health check
- `GET /api/library/<steam_id>` - Fetch user's library
- `POST /api/recommendations/<steam_id>` - Get recommendations

## Next Steps
- [ ] Add genre filtering
- [ ] Integrate IGDB for completion times
- [ ] Add hardware compatibility checks
- [ ] Implement user preferences storage
- [ ] Create authentication system