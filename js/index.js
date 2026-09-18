// js/index.js
document.addEventListener('DOMContentLoaded', () => {
    // If logged in, redirect to dashboard
    if (api.getToken()) {
        window.location.href = 'dashboard.html';
        return;
    }

    const loginModal = document.getElementById('login-modal');
    const registerModal = document.getElementById('register-modal');

    document.getElementById('nav-login').addEventListener('click', (e) => {
        e.preventDefault();
        loginModal.showModal();
    });

    document.getElementById('nav-register').addEventListener('click', (e) => {
        e.preventDefault();
        registerModal.showModal();
    });

    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const errorDiv = document.getElementById('login-error');
        errorDiv.style.display = 'none';
        
        try {
            const res = await api.fetchJSON('/api/auth/login', {
                method: 'POST',
                body: JSON.stringify({
                    username: document.getElementById('login-username').value,
                    password: document.getElementById('login-password').value
                })
            });
            api.setToken(res.access_token);
            window.location.href = 'dashboard.html';
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    });

    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const errorDiv = document.getElementById('register-error');
        errorDiv.style.display = 'none';
        
        try {
            const res = await api.fetchJSON('/api/auth/register', {
                method: 'POST',
                body: JSON.stringify({
                    username: document.getElementById('reg-username').value,
                    email: document.getElementById('reg-email').value,
                    password: document.getElementById('reg-password').value,
                    college_campus: document.getElementById('reg-campus').value,
                    academic_section: document.getElementById('reg-section').value
                })
            });
            api.setToken(res.access_token);
            window.location.href = 'dashboard.html';
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    });
});
