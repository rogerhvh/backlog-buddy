// frontend/app.js
const API_BASE_URL = '/api';

// STATIC TEST DATA - Remove this section when connecting to real API
const USE_STATIC_DATA = true; // Set to false when using real API
const STATIC_TEST_DATA = {
    success: true,
    recommendations: [
        {
            appid: 730,
            name: "Counter-Strike 2",
            playtime_forever: 82608, // 1376.8 hours in minutes
            playtime_2weeks: 246,      // 4.1 hours in minutes
            recommendation_score: 223,
            genres: "Action,FPS,Multiplayer,Competitive"
        },
        {
            appid: 440,
            name: "Team Fortress 2",
            playtime_forever: 43038, // 717.3 hours in minutes
            playtime_2weeks: 0,
            recommendation_score: 156,
            genres: "Action,FPS,Multiplayer,Team-Based"
        },
        {
            appid: 570,
            name: "Dota 2",
            playtime_forever: 32592, // 543.2 hours in minutes
            playtime_2weeks: 750,     // 12.5 hours in minutes
            recommendation_score: 189,
            genres: "MOBA,Strategy,Multiplayer,Competitive"
        },
        {
            appid: 1091500,
            name: "Cyberpunk 2077",
            playtime_forever: 4560,  // 76 hours in minutes
            playtime_2weeks: 120,    // 2 hours in minutes
            recommendation_score: 145,
            genres: "RPG,Open World,Action,Story Rich"
        },
        {
            appid: 1174180,
            name: "Red Dead Redemption 2",
            playtime_forever: 7200,  // 120 hours in minutes
            playtime_2weeks: 0,
            recommendation_score: 132,
            genres: "Action,Adventure,Open World,Western"
        }
    ]
};

document.getElementById('getRecommendations').addEventListener('click', async () => {
    const steamId = document.getElementById('steamId').value.trim();
    const timeAvailable = parseInt(document.getElementById('timeAvailable').value);

    if (!steamId) {
        showError('Please enter a valid Steam ID');
        return;
    }

    hideAllSections();
    showLoading();

    try {
        let data;
        
        // Use static data for testing if enabled
        if (USE_STATIC_DATA) {
            // Simulate API delay
            await new Promise(resolve => setTimeout(resolve, 1000));
            data = STATIC_TEST_DATA;
        } else {
            // Real API call
            const response = await fetch(`${API_BASE_URL}/recommendations/${steamId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    time_available: timeAvailable
                })
            });
            data = await response.json();
        }

        if (!data.success) {
            throw new Error(data.error || 'Failed to fetch recommendations');
        }

        displayRecommendations(data.recommendations);
    } catch (error) {
        showError(error.message);
    }
});

// Add enter key support
document.getElementById('steamId').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') document.getElementById('getRecommendations').click();
});

document.getElementById('timeAvailable').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') document.getElementById('getRecommendations').click();
});

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});

function displayRecommendations(games) {
    hideAllSections();
    
    const gameList = document.getElementById('gameList');
    gameList.innerHTML = '';

    games.forEach((game, index) => {
        const card = createGameCard(game, index + 1);
        gameList.appendChild(card);
    });

    document.getElementById('results').style.display = 'block';
}

function createGameCard(game, rank) {
    const card = document.createElement('div');
    card.className = 'game-card';
    
    const hoursPlayed = Math.round(game.playtime_forever / 60 * 10) / 10;
    const hours2Weeks = Math.round((game.playtime_2weeks || 0) / 60 * 10) / 10;
    
    // Parse genres - handle both comma-separated string and array
    let genres = [];
    if (game.genres) {
        if (typeof game.genres === 'string') {
            genres = game.genres.split(',').map(g => g.trim());
        } else if (Array.isArray(game.genres)) {
            genres = game.genres;
        }
    }
    
    // Get Steam header image - construct URL from app_id/appid if available
    const appId = game.app_id || game.appid;
    const backgroundImage = game.header_image || 
                          (appId ? `https://cdn.akamai.steamstatic.com/steam/apps/${appId}/header.jpg` : '');
    
    card.innerHTML = `
        <div class="game-card-content">
            <div class="rank-badge">#${rank}</div>
            <h3 class="game-title">${game.name}</h3>
            
            <div class="game-stats">
                <div class="stat">
                    <span class="stat-label">Total Hours</span>
                    <span class="stat-value">${hoursPlayed}h</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Recent</span>
                    <span class="stat-value">${hours2Weeks}h</span>
                </div>
            </div>

            ${genres.length > 0 ? `
                <div class="genre-tags">
                    ${genres.slice(0, 3).map(genre => `
                        <span class="genre-tag">${genre}</span>
                    `).join('')}
                    ${genres.length > 3 ? `<span class="genre-tag">+${genres.length - 3}</span>` : ''}
                </div>
            ` : ''}

            <div class="score-display">
                ${backgroundImage ? `<div class="score-display-bg" style="background-image: url('${backgroundImage}');"></div>` : ''}
                <div class="score-label">Match Score</div>
                <div class="score-value">${Math.round(game.recommendation_score)}</div>
            </div>

            <button class="view-details-btn" onclick="openModal(${rank - 1})">
                View Details
            </button>
        </div>
    `;
    
    return card;
}

// Store current games data for modal access
let currentGames = [];

function displayRecommendationsWithData(games) {
    currentGames = games;
    displayRecommendations(games);
}

// Update the main display function to store games
const originalDisplayRecommendations = displayRecommendations;
displayRecommendations = function(games) {
    currentGames = games;
    originalDisplayRecommendations(games);
};

function openModal(gameIndex) {
    const game = currentGames[gameIndex];
    if (!game) return;

    const hoursPlayed = Math.round(game.playtime_forever / 60 * 10) / 10;
    const hours2Weeks = Math.round((game.playtime_2weeks || 0) / 60 * 10) / 10;
    
    // Parse genres
    let genres = [];
    if (game.genres) {
        if (typeof game.genres === 'string') {
            genres = game.genres.split(',').map(g => g.trim());
        } else if (Array.isArray(game.genres)) {
            genres = game.genres;
        }
    }

    // Get background image
    const appId = game.app_id || game.appid;
    const backgroundImage = game.header_image || 
                          (appId ? `https://cdn.akamai.steamstatic.com/steam/apps/${appId}/header.jpg` : '');

    document.getElementById('modalTitle').textContent = game.name;
    
    if (backgroundImage) {
        document.getElementById('modalBg').style.backgroundImage = `url('${backgroundImage}')`;
    }
    
    // Build stats HTML
    let statsHTML = `
        <div class="modal-stat">
            <div class="modal-stat-label">Total Hours</div>
            <div class="modal-stat-value">${hoursPlayed}h</div>
        </div>
        <div class="modal-stat">
            <div class="modal-stat-label">Recent Hours</div>
            <div class="modal-stat-value">${hours2Weeks}h</div>
        </div>
        <div class="modal-stat">
            <div class="modal-stat-label">Match Score</div>
            <div class="modal-stat-value">${Math.round(game.recommendation_score)}</div>
        </div>
        <div class="modal-stat">
            <div class="modal-stat-label">Rank</div>
            <div class="modal-stat-value">#${gameIndex + 1}</div>
        </div>
    `;

    // Add additional stats if available
    if (game.avg_session_length) {
        statsHTML += `
            <div class="modal-stat">
                <div class="modal-stat-label">Avg Session</div>
                <div class="modal-stat-value">${Math.round(game.avg_session_length)}m</div>
            </div>
        `;
    }

    if (game.last_played) {
        const lastPlayed = new Date(game.last_played * 1000).toLocaleDateString();
        statsHTML += `
            <div class="modal-stat">
                <div class="modal-stat-label">Last Played</div>
                <div class="modal-stat-value">${lastPlayed}</div>
            </div>
        `;
    }

    document.getElementById('modalStats').innerHTML = statsHTML;

    // Display genres
    if (genres.length > 0) {
        document.getElementById('modalGenres').innerHTML = genres.map(genre => `
            <span class="modal-genre-tag">${genre}</span>
        `).join('');
    } else {
        document.getElementById('modalGenres').innerHTML = '<p style="color: var(--text-muted);">No genre information available</p>';
    }

    // Show Steam store link if app_id/appid is available
    const additionalInfoEl = document.getElementById('modalAdditionalInfo');
    if (appId) {
        additionalInfoEl.innerHTML = `
            <a href="https://store.steampowered.com/app/${appId}" 
               target="_blank" 
               class="steam-link">
                View on Steam Store →
            </a>
        `;
    } else {
        additionalInfoEl.innerHTML = '';
    }

    document.getElementById('modalOverlay').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal(event) {
    if (!event || event.target === document.getElementById('modalOverlay') || event === true) {
        document.getElementById('modalOverlay').classList.remove('active');
        document.body.style.overflow = '';
    }
}

function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function showError(message) {
    hideAllSections();
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('error').style.display = 'block';
}

function hideAllSections() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').style.display = 'none';
    document.getElementById('error').style.display = 'none';
}