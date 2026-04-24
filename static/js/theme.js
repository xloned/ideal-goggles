// Theme toggle: v1 (classic) / v2 (modern)
(function() {
    const STORAGE_KEY = 'arm-theme';
    const DEFAULT_THEME = 'theme-v1';

    function getTheme() {
        return localStorage.getItem(STORAGE_KEY) || DEFAULT_THEME;
    }

    function setTheme(theme) {
        localStorage.setItem(STORAGE_KEY, theme);
        document.body.className = theme;
        // Update toggle button labels
        document.querySelectorAll('.theme-toggle').forEach(btn => {
            btn.textContent = theme === 'theme-v1' ? 'Дизайн 2' : 'Дизайн 1';
        });
    }

    function toggleTheme() {
        const current = getTheme();
        setTheme(current === 'theme-v1' ? 'theme-v2' : 'theme-v1');
    }

    // Apply theme immediately (before DOM ready, body class set via inline script)
    // Bind toggle buttons after DOM loads
    document.addEventListener('DOMContentLoaded', function() {
        setTheme(getTheme());
        document.querySelectorAll('.theme-toggle').forEach(btn => {
            btn.addEventListener('click', toggleTheme);
        });
    });

    // Expose for inline use
    window.toggleTheme = toggleTheme;
    window.getTheme = getTheme;
})();
