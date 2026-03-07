// frontend/app.js
const API_BASE_URL = '/api';

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
        const response = await fetch(`${API_BASE_URL}/recommendations/${steamId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                time_available: timeAvailable
            })
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Failed to fetch recommendations');
        }

        displayRecommendations(data.recommendations);
    } catch (error) {
        showError(error.message);
    }
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
    
    card.innerHTML = `
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

        <div class="score-display">
            <div class="score-label">Match Score</div>
            <div class="score-value">${Math.round(game.recommendation_score)}</div>
        </div>
    `;
    
    return card;
}

let currentGames = [];

function displayRecommendationsData(games) {
    currentGames = games;
    displayRecommendations(games);
}

const originalDisplayRecommendations = displayRecommendations;

displayRecommendations = function(games) {
    currentGames = games;
    originalDisplayRecommendations(games);
}

function openModal(gameIndex) {
    const game = currentGames[gameIndex];
    if (!game) return;

    const hoursPlayed = Math.round(game.playtime_forever / 60 * 10) / 10;
    const hours2Weeks = Math.round((game.playtime_2weeks || 0) / 60 * 10) / 10;

    let genre = [];
    if (game.genres) {
        if (typeof game.genres === 'string') {
            genre = game.genres.split(',').map(g => g.trim());
        } else if (Array.isArray(game.genres)) {
            genre = game.genres;
        }
    }

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