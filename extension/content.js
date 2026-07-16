/**
 * Impossible Extension - Content Script
 * 
 * Injected into pages on https://the-impossible.onrender.com/*
 * Handles communication between web page and extension
 */

(function() {
    'use strict';
    
    console.log('[Impossible Extension] Content script loaded!');
    console.log('[Impossible Extension] Page:', window.location.href);
    
    // Listen for messages from the web page
    window.addEventListener('message', (event) => {
        // Only accept messages from same origin
        if (event.source !== window) return;
        
        if (event.data.type === 'EXTENSION_REQUEST') {
            console.log('[Impossible Extension] Received request:', event.data);
            
            // Forward to background script
            chrome.runtime.sendMessage({
                action: event.data.action || 'authenticate'
            }, (response) => {
                // Send response back to page
                window.postMessage({
                    type: 'EXTENSION_RESPONSE',
                    data: response
                }, '*');
            });
        }
    });
    
    // Listen for messages from background script
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.type === 'EXTENSION_AUTH_SUCCESS') {
            // Forward success to page
            window.postMessage({
                type: 'EXTENSION_AUTH_SUCCESS',
                token: message.token
            }, '*');
        }
    });
    
    // Inject indicator into page
    function injectIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'extension-indicator';
        indicator.innerHTML = `
            <div style="
                position: fixed;
                bottom: 10px;
                right: 10px;
                background: rgba(0, 0, 0, 0.8);
                color: #00ff00;
                padding: 5px 10px;
                border-radius: 5px;
                font-family: monospace;
                font-size: 12px;
                z-index: 999999;
                border: 1px solid #00ff00;
            ">
                ⚡ Extension Active
            </div>
        `;
        document.body.appendChild(indicator);
        
        // Remove after 3 seconds
        setTimeout(() => {
            indicator.remove();
        }, 3000);
    }
    
    // Inject indicator when page loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectIndicator);
    } else {
        injectIndicator();
    }
    
    // Expose extension info to console
    console.log('[Impossible Extension] Info:');
    console.log('- Extension ID:', chrome.runtime.id);
    console.log('- API Key: IMPOSSIBLE_EXT_2024');
    console.log('- Endpoint: /api/extension-secret');
    console.log('- To authenticate: window.postMessage({type: "EXTENSION_REQUEST", action: "authenticate"}, "*")');
})();
