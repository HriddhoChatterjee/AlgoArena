let queueInterval;
let wsManager = null;

document.addEventListener('DOMContentLoaded', async () => {
    if (!api.getToken()) {
        window.location.href = 'index.html';
        return;
    }
    
    document.getElementById('nav-logout').onclick = (e) => { 
        e.preventDefault(); 
        api.logout(); 
    };
    
    try { 
        const u = await api.fetchJSON('/api/user/me'); 
        ['name','level','elo','solved'].forEach(k => {
            const keyMap = {name:'username',level:'level',elo:'elo_rating',solved:'total_solved'};
            document.getElementById(`profile-${k}`).textContent = u[keyMap[k]];
        }); 
        document.getElementById('profile-streak').textContent = `${u.current_streak} days`; 
        document.getElementById('profile-xp').textContent = `${u.xp} / ${u.xp_to_next} XP`; 
        document.getElementById('xp-fill').style.width = `${Math.min(100,u.xp/u.xp_to_next*100)}%`; 
    } catch(e) { 
        console.error(e); 
    }
    
    // Solo Modes
    document.querySelectorAll('.mode-card[data-mode]').forEach(card => {
        card.onclick = async () => { 
            document.getElementById('loading-modal').showModal(); 
            try { 
                const game = await api.fetchJSON('/api/solo/start', {
                    method:'POST',
                    body:JSON.stringify({mode:card.dataset.mode})
                }); 
                sessionStorage.setItem('currentMatchId', game.match_id);
                sessionStorage.setItem('problemData', JSON.stringify(game.problem));
                sessionStorage.setItem('botData', JSON.stringify(game.bot));
                window.location.href='arena.html'; 
            } catch(e) { 
                document.getElementById('loading-modal').close(); 
                alert(e.message); 
            } 
        };
    });

    // Multiplayer Matchmaking
    const findMatchBtn = document.getElementById('find-match-btn');
    if (findMatchBtn) {
        findMatchBtn.onclick = () => {
            const mmModal = document.getElementById('matchmaking-modal');
            mmModal.showModal();
            let seconds = 0;
            const timerEl = document.getElementById('queue-timer');
            timerEl.textContent = '0';
            queueInterval = setInterval(() => {
                seconds++;
                timerEl.textContent = seconds;
            }, 1000);

            wsManager = new ArenaWebSocket('matchmaking', api.getUserId());
            wsManager.onMessage = (data) => {
                if (data.type === 'match_found') {
                    clearInterval(queueInterval);
                    mmModal.close();
                    sessionStorage.setItem('currentMatchId', data.match_id);
                    sessionStorage.setItem('problemData', JSON.stringify(data.problem));
                    sessionStorage.removeItem('botData');
                    window.location.href = 'arena.html';
                }
            };
            wsManager.connect();
        };
    }
});

window.cancelMatchmaking = function() {
    clearInterval(queueInterval);
    const mmModal = document.getElementById('matchmaking-modal');
    if (mmModal) mmModal.close();
    if (wsManager) wsManager.disconnect();
};
