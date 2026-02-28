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

    card.innerHTML = `
        <div>#${rank}</div>
        <div class="game-name">${game.name || 'Unknown game'}</div>
        <div class="game-stats">
            <span>${hoursPlayed}h total</span>
            <span>${hours2Weeks}h recently</span>
            <span>Score: ${Math.round(game.recommendation_score || 0)}</span>
        </div>
    `;

    return card;
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
