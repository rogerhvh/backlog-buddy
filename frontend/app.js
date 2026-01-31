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
        <div>#${rank}</div>
        <div class="game-name">${game.name}</div>
        <div class="game-stats">
            <span>${hoursPlayed}h total</span>
            <span>${hours2Weeks}h recently</span>
            <span>Score: ${Math.round(game.recommendation_score)}</span>
            <p>Genres: ${game.genres}</p>
        </div>
    `;
    return card;
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