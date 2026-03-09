// frontend/app.js
const API_BASE_URL = '/api';

let currentProfile = null;

function showSection(sectionId) {
    document.getElementById('recommendations-section').style.display = sectionId === 'recommendations-section' ? 'block' : 'none';
    document.getElementById('profile-section').style.display = sectionId === 'profile-section' ? 'block' : 'none';
    hideFeedbackSections();
}

window.showSection = showSection;

document.getElementById('createProfile').addEventListener('click', async () => {
    const steamId = document.getElementById('createSteamId').value.trim();
    const userId = document.getElementById('createUserId').value.trim();

    if (!steamId) {
        showError('Please enter your Steam ID first.');
        return;
    }

    if (!userId) {
        showError('Please create a username.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/profile`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                steam_id: steamId,
                preferred_genres: [],
                min_playtime_hours: null,
                max_playtime_hours: null
            })
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Failed to create profile');
        }

        currentProfile = data.profile;
        displayProfile(currentProfile);
        document.getElementById('profileEditSection').style.display = 'block';
        document.getElementById('profileDataSection').style.display = 'block';
        document.getElementById('loadUserId').value = currentProfile.user_id;
        document.getElementById('recommendationUserId').value = currentProfile.user_id;
    } catch (error) {
        showError('Error creating profile: ' + error.message);
    }
});

document.getElementById('getRecommendations').addEventListener('click', async () => {
    const userId = document.getElementById('recommendationUserId').value.trim();
    const timeAvailable = parseInt(document.getElementById('timeAvailable').value);

    if (!userId) {
        showError('Please enter your User ID. You must create a profile first.');
        return;
    }

    hideFeedbackSections();
    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/recommendations/${userId}`, {
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

document.getElementById('loadProfile').addEventListener('click', async () => {
    const userId = document.getElementById('loadUserId').value.trim();

    if (!userId) {
        showError('Please enter a User ID');
        return;
    }

    hideFeedbackSections();

    try {
        const response = await fetch(`${API_BASE_URL}/profile/${userId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();

        if (data.success) {
            currentProfile = data.profile;
            displayProfile(currentProfile);
            document.getElementById('profileEditSection').style.display = 'block';
            document.getElementById('profileDataSection').style.display = 'block';
            document.getElementById('recommendationUserId').value = currentProfile.user_id;
        } else {
            currentProfile = null;
            document.getElementById('profileEditSection').style.display = 'none';
            document.getElementById('profileDataSection').style.display = 'none';
            clearProfileForm();
            throw new Error(data.error || 'Profile not found');
        }
    } catch (error) {
        showError('Error loading profile: ' + error.message);
    }
});

document.getElementById('saveProfile').addEventListener('click', async () => {
    const steamId = document.getElementById('profileSteamId').value.trim();
    const genresText = document.getElementById('preferredGenres').value.trim();
    const minPlaytime = document.getElementById('minPlaytime').value ? parseInt(document.getElementById('minPlaytime').value) : null;
    const maxPlaytime = document.getElementById('maxPlaytime').value ? parseInt(document.getElementById('maxPlaytime').value) : null;

    if (!currentProfile) {
        showError('Please create or load a profile first.');
        return;
    }

    if (!steamId) {
        showError('Steam ID is required');
        return;
    }

    const genres = genresText ? genresText.split(',').map(g => g.trim()).filter(Boolean) : [];

    try {
        const url = `${API_BASE_URL}/profile/${currentProfile.user_id}`;
        const method = 'PUT';
        const body = {
            steam_id: steamId,
            preferred_genres: genres,
            min_playtime_hours: minPlaytime,
            max_playtime_hours: maxPlaytime
        };

        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Failed to save profile');
        }

        currentProfile = data.profile;
        displayProfile(currentProfile);
        document.getElementById('profileDataSection').style.display = 'block';
    } catch (error) {
        showError('Error saving profile: ' + error.message);
    }
});

document.getElementById('deleteProfile').addEventListener('click', async () => {
    if (!currentProfile) {
        showError('Please create or load a profile first.');
        return;
    }

    if (!confirm('Are you sure you want to delete this profile?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/profile/${currentProfile.user_id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Failed to delete profile');
        }

        currentProfile = null;
        clearProfileForm();
        document.getElementById('profileEditSection').style.display = 'none';
        document.getElementById('profileDataSection').style.display = 'none';
        document.getElementById('recommendationUserId').value = '';
    } catch (error) {
        showError('Error deleting profile: ' + error.message);
    }
});

function displayProfile(profile) {
    document.getElementById('displayUserId').textContent = profile.user_id || '';
    document.getElementById('displaySteamId').textContent = profile.steam_id || '';
    document.getElementById('displayGenres').textContent = (profile.preferred_genres || []).join(', ') || 'None';
    document.getElementById('displayMinPlaytime').textContent = profile.min_playtime_hours ?? 'No limit';
    document.getElementById('displayMaxPlaytime').textContent = profile.max_playtime_hours ?? 'No limit';
    document.getElementById('displayCreatedDate').textContent = profile.creation_date || '';
    document.getElementById('displayUpdatedDate').textContent = profile.last_updated || '';

    document.getElementById('profileSteamId').value = profile.steam_id || '';
    document.getElementById('preferredGenres').value = (profile.preferred_genres || []).join(', ');
    document.getElementById('minPlaytime').value = profile.min_playtime_hours ?? '';
    document.getElementById('maxPlaytime').value = profile.max_playtime_hours ?? '';
}

function clearProfileForm() {
    document.getElementById('profileSteamId').value = '';
    document.getElementById('preferredGenres').value = '';
    document.getElementById('minPlaytime').value = '';
    document.getElementById('maxPlaytime').value = '';
    document.getElementById('createSteamId').value = '';
    document.getElementById('createUserId').value = '';
    document.getElementById('loadUserId').value = '';
}

// Add enter key support for recommendation section
document.getElementById('recommendationUserId').addEventListener('keypress', (e) => {
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
    hideFeedbackSections();

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

    const hoursPlayed = Math.round((game.playtime_forever || 0) / 60 * 10) / 10;
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
    hideFeedbackSections();
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('error').style.display = 'block';
}

function hideFeedbackSections() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').style.display = 'none';
    document.getElementById('error').style.display = 'none';
}
