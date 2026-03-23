// Custom JavaScript for sglawwatch database
// Following Zeeker customization guide best practices

// Defensive programming - ensure we're on the right database (per guide)
function isDatabasePage() {
    return window.location.pathname.includes('/sglawwatch') ||
           document.body.dataset.database === 'sglawwatch';
}

document.addEventListener('DOMContentLoaded', function() {
    if (!isDatabasePage()) {
        return; // Exit if not our database (safety per guide)
    }

    console.log('Custom JS loaded for sglawwatch database');

    // Initialize custom features safely
    initCustomFeatures();
});

function initCustomFeatures() {
    // Add custom search suggestions (safe implementation)
    const searchInput = document.querySelector('.hero-search-input');
    if (searchInput) {
        searchInput.placeholder = 'Search sglawwatch...';
    }

    // Custom table enhancements
    enhanceTables();
}

function enhanceTables() {
    // Safe element selection per guide
    const tables = document.querySelectorAll('.table-wrapper table');
    tables.forEach(table => {
        // Add your custom table functionality here
        table.classList.add('enhanced-table');
    });
}
