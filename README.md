# backlog-buddy
Steam backlog recommendation engine - helps you decide which game to play next based on playtime, engagement, and estimated completion time.

## Quick Start

### Prerequisites
- Python 3.8+
- Steam API key (get from https://steamcommunity.com/dev/apikey)

### Backend Setup

1. **Navigate to backend and create virtual environment:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
# Create .env file with:
STEAM_API_KEY=your_steam_api_key_here
FLASK_ENV=development
FLASK_DEBUG=True
```

4. **Run the server:**
```bash
python app.py
```

The backend will start on `http://localhost:5000`

### Frontend Setup

From the project root:
```bash
# Option 1: Simple HTTP server
cd frontend
python -m http.server 8000
# Visit http://localhost:8000

# Option 2: Open directly in browser
open frontend/index.html
```

## Getting Your Steam API Key

1. Go to https://steamcommunity.com/dev/apikey
2. Fill out the form (use `http://localhost` as the domain)
3. Copy the generated key to `backend/.env`

## Getting Your Steam ID

1. Go to https://steamid.io/
2. Enter your Steam profile URL or username
3. Copy the **steamID64** (17-digit number)

## Features

### Game Recommendation Engine
The app ranks your Steam library games using multiple factors:

- **Recent Playtime** (weight: 0.5) - Games you're actively playing
- **Total Playtime** (weight: 0.3) - Games you've invested time in (capped at 100h)
- **Started But Not Finished** (+20 points) - Games with 0-5 hours playtime
- **Completion Time Matching** (NEW) - Prioritizes games completable in available time:
  - **+30 points**: Game completable within your available time
  - **+15 points**: Game close to completable (1.5x available time)
  - **-5 points**: Game too long for available time
- **Time Availability** (+15 points) - For short sessions, prefer already-started games
- **Preferred Genre Match** (+25 / -5) - Boosts games matching profile `preferred_genres`
- **Profile Playtime Preferences** - Applies `min_playtime_hours` and `max_playtime_hours` using completion-time data when available

### Profile-Aware Recommendations
- Create a profile with `user_id`, `steam_id`, and optional preferences
- Recommendations are requested by `user_id` and automatically use that profile's settings
- Profile creation now proactively starts genre indexing for that user's library
- Profile creation response includes `genre_indexing_status` (`started`, `in_progress`, `up_to_date`, `failed`)

### Completion Time Data
Fetches estimated main story completion times from [HowLongToBeat](https://howlongtobeat.com/) using parallel requests for speed (up to 20 games).

## Project Structure
```
backlog-buddy/
├── backend/
│   ├── app.py                          # Flask server
│   ├── models.py                       # Data models
│   ├── requirements.txt                # Python dependencies
│   ├── .env                            # Configuration (git-ignored)
│   ├── database/
│   │   └── database.py                 # User profile DB access
│   ├── routes/
│   │   ├── game_routes.py              # Library + recommendation endpoints
│   │   └── profile_routes.py           # Profile CRUD endpoints
│   └── services/
│       ├── steam_services.py           # Steam API integration
│       ├── reccomendation_service.py   # Game ranking logic
│       ├── completion_time_service.py  # HowLongToBeat integration
│       ├── profile_service.py          # Profile business logic
│       └── runtime_services.py         # Shared singleton service instances
│   └── data/
│       └── game_database.py            # Handles database logic
│       └── index.py                    # Main Index class
│       └── index_processor.py          # Indexing work logic
│       └── search_processor.py         # Search work logic
│       └── tag_posting.py              # Posting object
│       └── games.db                    # Final games db
│       └── games_temp.db               # Games not merged with final db
│       └── tag_idf.backlog_buddy       # Tag -> IDF scores
│       └── index.backlog_buddy         # Inverted index for tags -> gameIDs
├── frontend/
│   ├── index.html                      # Main UI
│   └── app.js                          # Client-side logic
└── README.md
```

## API Endpoints

### Game Library
```
GET /api/library/<steam_id>
```
Returns owned games from Steam for a given account.

### Recommendations
```
POST /api/recommendations/<user_id>
```
Uses the profile's `steam_id` and preferences to return top recommendations.

**Request Body:**
```json
{
  "time_available": 120
}
```

### Profiles
```
POST   /api/profile
GET    /api/profile/<user_id>
PUT    /api/profile/<user_id>
DELETE /api/profile/<user_id>
GET    /api/profile/steam/<steam_id>
```

**Create Profile Body:**
```json
{
  "user_id": "my_username",
  "steam_id": "76561198000000000",
  "preferred_genres": ["action", "rpg"],
  "min_playtime_hours": null,
  "max_playtime_hours": null
}
```

**Create Profile Response (excerpt):**
```json
{
  "success": true,
  "genre_indexing_status": "started",
  "profile": {
    "user_id": "my_username",
    "steam_id": "76561198000000000"
  }
}
```

**Recommendation Response (excerpt):**
```json
{
  "success": true,
  "recommendations": [
    {
      "appid": 570,
      "name": "Dota 2",
      "playtime_forever": 4320,
      "playtime_2weeks": 120,
      "completion_time_hours": null,
      "recommendation_score": 95.5,
      "img_icon_url": "...",
      "img_logo_url": "..."
    }
  ]
}
```

## Development

### Activate Virtual Environment (every session)
```bash
source backend/.venv/bin/activate
```

To make it permanent, add to your shell profile (`~/.zshrc` or `~/.bash_profile`):
```bash
cd /path/to/backlog-buddy && source backend/.venv/bin/activate
```

### Dependencies
- **Flask** - Web framework
- **requests** - HTTP requests
- **python-dotenv** - Environment variables
- **howlongtobeatpy** - Game completion time estimates

## Roadmap / TODO

- [ ] Genre filtering
- [ ] Difficulty filtering  
- [ ] Store completion time data in database (reduce API calls)
- [ ] User accounts / save preferences
- [ ] Add game description/reviews
- [ ] Playstyle recommendations (story-focused, multiplayer, etc.)

## Known Issues

- HowLongToBeat searches can be imperfect for games with special characters (™, ®)
- Some games may not be in HowLongToBeat database
- First load is slower due to fetching completion times
- First recommendation request may still show missing genres while background indexing is in progress

## Troubleshooting

**"Module not found" errors:**
```bash
# Make sure venv is activated and dependencies installed
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

**Slow loading:**
The app fetches game metadata/genres and completion-time data in the background. First load can take longer depending on library size.

**Steam API errors:**
- Verify your API key in `backend/.env`
- Check that you're using the correct Steam ID (17-digit steamID64)
- Ensure your Steam profile is public

**Indexing Information**
The index is currently rebuilt upon every app launch. To stop this, comment out the two lines marked in backend/app.py. To run a manual rebuild, run manual_rebuild.py. 