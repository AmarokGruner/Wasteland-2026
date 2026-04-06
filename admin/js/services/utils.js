/**
 * Admin Utilities - Allgemeine Hilfsfunktionen
 * Extrahiert aus admin.html
 */

/**
 * Zeigt eine Snackbar-Nachricht
 */
export function showSnackbar(message, duration = 3000) {
    const snackbar = document.getElementById('snackbar');
    if (!snackbar) {
        console.log('Snackbar:', message);
        return;
    }
    
    snackbar.textContent = message;
    snackbar.classList.add('show');
    
    setTimeout(() => {
        snackbar.classList.remove('show');
    }, duration);
}

/**
 * HTML Escaping zum Schutz vor XSS
 */
export function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Formatierter Datums-String
 */
export function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('de-DE', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Kurzes Datum (TT.MM.JJJJ)
 */
export function formatDateShort(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE');
}

/**
 * Zeitdifferenz in Stunden
 */
export function hoursSince(dateString) {
    if (!dateString) return null;
    const now = new Date();
    const then = new Date(dateString);
    const diff = (now - then) / (1000 * 60 * 60); // Stunden
    return Math.max(0, Math.floor(diff));
}

/**
 * Debounce Funktion für Such-Inputs
 */
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Copy to Clipboard
 */
export function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showSnackbar('✅ In Zwischenablage kopiert');
    }).catch(err => {
        console.error('Copy failed:', err);
        alert('Kopieren fehlgeschlagen');
    });
}

/**
 * Konfirmation mit Custom Message
 */
export function confirmWithMessage(message, confirmText = 'Bestätigen') {
    const userConfirm = window.confirm(message);
    return userConfirm;
}

// Globale Funktionen
window.showSnackbar = showSnackbar;
window.escapeHtml = escapeHtml;
window.formatDate = formatDate;
window.formatDateShort = formatDateShort;
