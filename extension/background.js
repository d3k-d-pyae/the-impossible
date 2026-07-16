/**
 * Impossible Extension - Background Service Worker
 * 
 * This extension is part of Step 3 of the Impossible Challenge.
 * It communicates with the challenge server to obtain authentication tokens.
 * 
 * Key features:
 * - Hardcoded API key: IMPOSSIBLE_EXT_2024
 * - Calls /api/extension-secret endpoint
 * - Stores tokens in extension storage
 */

// API Configuration
const API_CONFIG = {
    baseUrl: '{{RENDER_URL}}',
    endpoint: '/api/extension-secret',
    apiKey: 'IMPOSSIBLE_EXT_2024'
};

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
    console.log('[Impossible Extension] Installed!');
    console.log('[Impossible Extension] API Key:', API_CONFIG.apiKey);
    console.log('[Impossible Extension] Endpoint:', API_CONFIG.endpoint);
});

// Listen for messages from popup or content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'authenticate') {
        authenticateWithServer()
            .then(data => {
                console.log('[Impossible Extension] Auth response:', data);
                sendResponse({ success: true, data: data });
            })
            .catch(error => {
                console.error('[Impossible Extension] Auth error:', error);
                sendResponse({ success: false, error: error.message });
            });
        return true; // Keep message channel open for async response
    }
    
    if (request.action === 'getToken') {
        chrome.storage.local.get('authToken', (result) => {
            sendResponse({ token: result.authToken });
        });
        return true;
    }
});

/**
 * Authenticate with the challenge server
 */
async function authenticateWithServer() {
    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoint}`;
    
    console.log('[Impossible Extension] Connecting to:', url);
    console.log('[Impossible Extension] Using API key:', API_CONFIG.apiKey);
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Extension-Key': API_CONFIG.apiKey
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('[Impossible Extension] Success!', data);
        
        // Store the token
        if (data.token) {
            chrome.storage.local.set({ authToken: data.token });
            console.log('[Impossible Extension] Token stored:', data.token);
        }
        
        return data;
    } catch (error) {
        console.error('[Impossible Extension] Request failed:', error);
        throw error;
    }
}

/**
 * Check if extension is properly configured
 */
function checkExtensionConfig() {
    console.log('[Impossible Extension] Configuration check:');
    console.log('- API Key:', API_CONFIG.apiKey);
    console.log('- Base URL:', API_CONFIG.baseUrl);
    console.log('- Endpoint:', API_CONFIG.endpoint);
    console.log('- Permissions:', chrome.runtime.getManifest().permissions);
}

// Run config check on startup
checkExtensionConfig();
