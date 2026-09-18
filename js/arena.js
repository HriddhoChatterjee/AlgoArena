// js/arena.js
let editor;
let wsManager;
let currentProblemData;

document.addEventListener('DOMContentLoaded', () => {
    const matchId = sessionStorage.getItem('currentMatchId');
    const problemRaw = sessionStorage.getItem('problemData');
    const userId = api.getUserId();

    if (!matchId || !problemRaw || !userId) {
        window.location.href = 'dashboard.html';
        return;
    }

    currentProblemData = JSON.parse(problemRaw);
    const bot = JSON.parse(sessionStorage.getItem('botData') || 'null');
    const botHud = document.getElementById('bot-hud');
    if (bot) {
        document.getElementById('bot-name').textContent = bot.name;
        document.getElementById('bot-level').textContent = `LEVEL ${bot.level} · ${currentProblemData.mode_label || 'SOLO ARENA'}`;
        const started = Date.now();
        setInterval(() => {
            const progress = Math.min(94, ((Date.now() - started) / (bot.eta_seconds * 1000)) * 100);
            document.getElementById('bot-progress').style.width = `${progress}%`;
            document.getElementById('bot-status').textContent = progress > 65 ? 'Testing an optimized approach...' : 'Mapping solution patterns...';
        }, 1000);
    } else if (botHud) {
        botHud.style.display = 'none';
    }
    
    // UI Elements
    document.getElementById('prob-title').textContent = currentProblemData.title;
    document.getElementById('prob-diff').textContent = currentProblemData.difficulty.toUpperCase();
    document.getElementById('prob-narrative').textContent = currentProblemData.story_narrative;
    
    const constraintsUl = document.getElementById('prob-constraints');
    currentProblemData.constraints.forEach(c => {
        const li = document.createElement('li');
        li.textContent = c;
        constraintsUl.appendChild(li);
    });

    const publicTests = currentProblemData.test_cases.filter(tc => !tc.is_hidden);
    let testText = '';
    publicTests.forEach((tc, i) => {
        testText += `Test ${i+1}:\nInput: ${tc.input}\nExpected: ${tc.expected_output}\n\n`;
    });
    document.getElementById('prob-tests').textContent = testText;

    // Initialize CodeMirror
    editor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
        mode: 'python',
        theme: 'monokai',
        lineNumbers: true,
        indentUnit: 4,
        matchBrackets: true
    });
    
    // Populate starter code
    editor.setValue(currentProblemData.starter_templates.python || '# Write your Python code here');

    const langSelect = document.getElementById('lang-select');
    langSelect.addEventListener('change', (e) => {
        const lang = e.target.value;
        if (lang === 'python') {
            editor.setOption('mode', 'python');
            editor.setValue(currentProblemData.starter_templates.python || '');
        } else if (lang === 'cpp') {
            editor.setOption('mode', 'text/x-c++src');
            editor.setValue(currentProblemData.starter_templates.cpp || '');
        } else if (lang === 'javascript') {
            editor.setOption('mode', 'javascript');
            editor.setValue(currentProblemData.starter_templates.javascript || '');
        }
    });

    // Focus Mode Toggle
    document.getElementById('focus-toggle').addEventListener('click', () => {
        document.body.classList.toggle('focus-mode');
        // Future iteration: Insert an embedded iframe audio player here
    });

    // WebSockets for live match state
    wsManager = new ArenaWebSocket(matchId, userId);
    wsManager.onMessage = (msg) => {
        if (msg.type === 'code_submission') {
            document.getElementById('shoutcast-text').textContent = msg.commentary;
            if (msg.match_completed) {
                showGameOverModal(msg.user_id === userId);
            }
        }
        if (msg.type === 'player_disconnected' && msg.user_id !== userId) {
            document.getElementById('shoutcast-text').textContent = "Opponent disconnected! You win by default.";
            showGameOverModal(true);
        }
    };
    wsManager.connect();

    // Submit Action
    document.getElementById('btn-submit').addEventListener('click', async () => {
        const code = editor.getValue();
        const lang = langSelect.value;
        const consoleEl = document.getElementById('output-console');
        
        consoleEl.innerHTML = "> Submitting code to Judges...<br>";
        
        try {
            const result = await api.fetchJSON('/api/match/submit', {
                method: 'POST',
                body: JSON.stringify({
                    match_id: matchId,
                    user_id: userId,
                    source_code: code,
                    language: lang
                })
            });
            
            consoleEl.innerHTML += `<span style="color: var(--accent-primary)">Verdict: ${result.passed ? 'ACCEPTED' : 'REJECTED'}</span><br>`;
            if (result.progression) {
                consoleEl.innerHTML += `<span style="color: var(--success)">+${result.progression.reward} XP · LEVEL ${result.progression.level}</span><br>`;
            }
            result.results.forEach((r, i) => {
                const color = r.status === 'Accepted' ? 'var(--success)' : 'var(--error)';
                consoleEl.innerHTML += `Test ${i+1}: <span style="color:${color}">${r.status}</span> (Time: ${r.time || '0.0'}s)<br>`;
                if (r.compile_output) {
                    consoleEl.innerHTML += `<span style="color:var(--error)">${r.compile_output}</span><br>`;
                }
            });
            
        } catch (error) {
            consoleEl.innerHTML += `<span style="color: var(--error)">Error: ${error.message}</span><br>`;
        }
    });
});

function showGameOverModal(isWinner) {
    const modal = document.getElementById('match-over-modal');
    const title = document.getElementById('match-over-title');
    const desc = document.getElementById('match-over-desc');
    
    if (isWinner) {
        title.textContent = "VICTORY";
        title.style.color = "var(--success)";
        desc.textContent = "You solved the challenge first! Elo +25";
    } else {
        title.textContent = "DEFEAT";
        title.style.color = "var(--error)";
        desc.textContent = "Your opponent solved the challenge. Elo -15";
    }
    
    modal.showModal();
    if (wsManager) wsManager.disconnect();
}
