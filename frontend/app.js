const CONFIG = {
    API_BASE: 'http://127.0.0.1:8000',
    POLL_INTERVAL: 3000
};

let pollIntervalId = null;

const elements = {
    startBtn: document.getElementById('start-btn'),
    stopBtn: document.getElementById('stop-btn'),
    statusIndicator: document.querySelector('.status-indicator'),
    statusText: document.getElementById('status-text'),
    balance: document.getElementById('account-balance'),
    trend: document.getElementById('market-trend'),
    rsi: document.getElementById('rsi-value'),
    signal: document.getElementById('active-signal'),
    console: document.getElementById('log-console')
};

function appendLog(message) {
    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.textContent = `[${timestamp}] ${message}`;
    elements.console.appendChild(entry);
    elements.console.scrollTop = elements.console.scrollHeight;
}

async function updateSystemState() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/status`);
        if (!response.ok) throw new Error('System unreachable');
        
        const data = await response.json();
        
        elements.statusIndicator.className = 'status-indicator online';
        elements.statusText.textContent = 'SYSTEM ONLINE';
        elements.balance.textContent = `$${parseFloat(data.account_balance).toFixed(2)}`;
        elements.trend.textContent = data.market_analysis.trend === 1 ? 'Bullish' : (data.market_analysis.trend === -1 ? 'Bearish' : 'Neutral');
        elements.rsi.textContent = parseFloat(data.market_analysis.rsi).toFixed(1);
        elements.signal.textContent = data.signal.action.toUpperCase();
        
    } catch (error) {
        elements.statusIndicator.className = 'status-indicator offline';
        elements.statusText.textContent = 'SYSTEM OFFLINE';
        appendLog('Error connecting to backend engine.');
    }
}

elements.startBtn.addEventListener('click', async () => {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/start`, { method: 'POST' });
        if (response.ok) {
            elements.startBtn.disabled = true;
            elements.stopBtn.disabled = false;
            appendLog('Engine initialized.');
            pollIntervalId = setInterval(updateSystemState, CONFIG.POLL_INTERVAL);
        }
    } catch (error) {
        appendLog('Failed to start engine.');
    }
});

elements.stopBtn.addEventListener('click', async () => {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/stop`, { method: 'POST' });
        if (response.ok) {
            clearInterval(pollIntervalId);
            elements.startBtn.disabled = false;
            elements.stopBtn.disabled = true;
            elements.statusIndicator.className = 'status-indicator offline';
            elements.statusText.textContent = 'SYSTEM OFFLINE';
            appendLog('Engine stopped.');
        }
    } catch (error) {
        appendLog('Failed to stop engine.');
    }
});

