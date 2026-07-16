/**
 * Impossible Extension - Popup Script
 */

document.addEventListener('DOMContentLoaded', () => {
    const status = document.getElementById('status');
    const authBtn = document.getElementById('authBtn');
    const configBtn = document.getElementById('configBtn');
    const wsBtn = document.getElementById('wsBtn');
    const tokenBox = document.getElementById('tokenBox');
    const tokenValue = document.getElementById('tokenValue');
    
    // Check for existing token
    chrome.storage.local.get('authToken', (result) => {
        if (result.authToken) {
            tokenValue.textContent = result.authToken;
            tokenBox.style.display = 'block';
            status.textContent = 'AUTHENTICATED';
            status.className = 'status ready';
        }
    });
    
    // Authenticate button
    authBtn.addEventListener('click', async () => {
        status.textContent = 'CONNECTING...';
        status.className = 'status connecting';
        authBtn.disabled = true;
        
        try {
            const response = await chrome.runtime.sendMessage({ action: 'authenticate' });
            
            if (response.success && response.data.token) {
                tokenValue.textContent = response.data.token;
                tokenBox.style.display = 'block';
                status.textContent = 'AUTHENTICATED!';
                status.className = 'status ready';
                
                // Notify content script
                chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                    if (tabs[0]) {
                        chrome.tabs.sendMessage(tabs[0].id, {
                            type: 'EXTENSION_AUTH_SUCCESS',
                            token: response.data.token
                        });
                    }
                });
            } else {
                status.textContent = 'AUTH FAILED';
                status.className = 'status error';
                console.error('Auth failed:', response);
            }
        } catch (error) {
            status.textContent = 'ERROR: ' + error.message;
            status.className = 'status error';
            console.error('Extension error:', error);
        }
        
        authBtn.disabled = false;
    });
    
    // Config button
    configBtn.addEventListener('click', () => {
        const config = `
            API Key: IMPOSSIBLE_EXT_2024
            Base URL: https://the-impossible.onrender.com
            Endpoint: /api/extension-secret
            Permissions: storage, tabs, activeTab
        `;
        alert(config);
    });
    
    // WebSocket button
    wsBtn.addEventListener('click', () => {
        chrome.storage.local.get('authToken', (result) => {
            if (result.authToken) {
                alert(`Connect to wss://the-impossible.onrender.com/ws with token: ${result.authToken}`);
            } else {
                alert('Authenticate first!');
            }
        });
    });
});
