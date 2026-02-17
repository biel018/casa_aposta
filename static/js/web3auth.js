/**
 * Web3 / MetaMask integration for Casa de Apostas
 * Handles: wallet connect, sign-in with Ethereum, link wallet
 */

class Web3Auth {
    constructor() {
        this.provider = null;
        this.signer = null;
        this.address = null;
        this.connected = false;
    }

    /**
     * Check if MetaMask is available
     */
    isMetaMaskInstalled() {
        return typeof window.ethereum !== 'undefined' && window.ethereum.isMetaMask;
    }

    /**
     * Connect MetaMask wallet
     */
    async connect() {
        if (!this.isMetaMaskInstalled()) {
            throw new Error('MetaMask não está instalado. Baixe em metamask.io');
        }

        try {
            this.provider = new ethers.BrowserProvider(window.ethereum);
            const accounts = await this.provider.send('eth_requestAccounts', []);
            this.signer = await this.provider.getSigner();
            this.address = await this.signer.getAddress();
            this.connected = true;
            return this.address;
        } catch (err) {
            if (err.code === 4001) {
                throw new Error('Conexão recusada pelo usuário');
            }
            throw err;
        }
    }

    /**
     * Sign In With Ethereum (SIWE)
     * 1. Get nonce from backend
     * 2. Sign message with MetaMask
     * 3. Verify signature on backend
     */
    async signIn() {
        if (!this.connected) {
            await this.connect();
        }

        // 1. Get nonce
        const nonceRes = await fetch(`/accounts/api/web3/nonce/?address=${this.address}`);
        const nonceData = await nonceRes.json();
        
        if (!nonceRes.ok) {
            throw new Error(nonceData.error || 'Erro ao obter nonce');
        }

        // 2. Build and sign message
        const message = `Casa de Apostas - Login\n\nAssine esta mensagem para autenticar.\n\nEndereço: ${this.address}\nNonce: ${nonceData.nonce}\nTimestamp: ${new Date().toISOString()}`;
        
        const signature = await this.signer.signMessage(message);

        // 3. Verify on backend
        const verifyRes = await fetch('/accounts/api/web3/verify/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                address: this.address,
                message: message,
                signature: signature,
            }),
        });

        const verifyData = await verifyRes.json();
        
        if (verifyData.success) {
            return verifyData;
        } else {
            throw new Error(verifyData.error || 'Falha na verificação');
        }
    }

    /**
     * Link wallet to existing account
     */
    async linkWallet() {
        if (!this.connected) {
            await this.connect();
        }

        const message = `Casa de Apostas - Vincular Carteira\n\nAssine para vincular: ${this.address}\nTimestamp: ${new Date().toISOString()}`;
        const signature = await this.signer.signMessage(message);

        const res = await fetch('/accounts/api/web3/link/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                address: this.address,
                message: message,
                signature: signature,
            }),
        });

        const data = await res.json();
        if (data.success) {
            return data;
        } else {
            throw new Error(data.error || 'Falha ao vincular');
        }
    }

    /**
     * Get short version of address
     */
    shortAddress() {
        if (!this.address) return '';
        return `${this.address.slice(0, 6)}...${this.address.slice(-4)}`;
    }
}

// Global instance
const web3Auth = new Web3Auth();

/**
 * Helper: get CSRF cookie
 */
function getCookie(name) {
    let value = null;
    document.cookie.split(';').forEach(c => {
        c = c.trim();
        if (c.startsWith(name + '=')) value = decodeURIComponent(c.substring(name.length + 1));
    });
    return value;
}

/**
 * UI: Connect MetaMask button click handler
 */
async function connectMetaMask() {
    const btn = document.getElementById('btnMetaMask');
    const status = document.getElementById('metamaskAuthStatus');

    if (!web3Auth.isMetaMaskInstalled()) {
        if (status) status.innerHTML = '<span class="text-danger small">MetaMask não encontrado. <a href="https://metamask.io" target="_blank">Instalar</a></span>';
        window.open('https://metamask.io', '_blank');
        return;
    }

    try {
        if (btn) btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Conectando...';
        
        const address = await web3Auth.connect();
        if (btn) {
            btn.innerHTML = `<i class="bi bi-wallet-fill"></i> ${web3Auth.shortAddress()}`;
            btn.classList.remove('btn-outline-warning');
            btn.classList.add('btn-warning');
        }

        // Check if user is logged in
        const isLoggedIn = document.body.dataset.loggedIn === 'true';
        
        if (isLoggedIn) {
            // Link wallet to account
            const result = await web3Auth.linkWallet();
            if (status) status.innerHTML = '<span class="text-success small"><i class="bi bi-check-circle"></i> Carteira vinculada!</span>';
        } else {
            // Sign in with MetaMask
            const result = await web3Auth.signIn();
            if (result.success) {
                window.location.reload();
            }
        }
    } catch (err) {
        console.error('MetaMask error:', err);
        if (btn) btn.innerHTML = '<i class="bi bi-wallet2"></i> MetaMask';
        if (status) status.innerHTML = `<span class="text-danger small">${err.message}</span>`;
    }
}

/**
 * Auto-detect MetaMask on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    const btn = document.getElementById('btnMetaMask');
    if (btn && !web3Auth.isMetaMaskInstalled()) {
        btn.title = 'MetaMask não detectado';
    }

    // Listen for account changes
    if (window.ethereum) {
        window.ethereum.on('accountsChanged', (accounts) => {
            if (accounts.length === 0) {
                if (btn) {
                    btn.innerHTML = '<i class="bi bi-wallet2"></i> MetaMask';
                    btn.classList.remove('btn-warning');
                    btn.classList.add('btn-outline-warning');
                }
                web3Auth.connected = false;
                web3Auth.address = null;
            } else {
                web3Auth.address = accounts[0];
                if (btn) btn.innerHTML = `<i class="bi bi-wallet-fill"></i> ${web3Auth.shortAddress()}`;
            }
        });
    }
});
