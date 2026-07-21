// Partner section JS files
// earnings.js
document.addEventListener('DOMContentLoaded', async function() {
    if (!requirePartner()) return;
    
    try {
        const data = await getWithAuth('/api/v1/partners/earnings');
        document.getElementById('totalEarnings').textContent = `$${data.total_earnings.toFixed(2)}`;
        document.getElementById('weeklyEarnings').textContent = `$${data.weekly_earnings.toFixed(2)}`;
        
        loadEarningsHistory(data.earnings_history);
    } catch (error) {
        console.error('Failed to load earnings:', error);
    }
});

function loadEarningsHistory(history) {
    // Implement earnings history display
    console.log('Earnings:', history);
}
