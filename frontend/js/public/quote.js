// Public section JS files
// quote.js - Quote calculation
function calculateQuote() {
    const form = document.getElementById('quoteFormComponent');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            pickup_zip: document.getElementById('quotePickupZip').value,
            delivery_zip: document.getElementById('quoteDeliveryZip').value,
            weight: parseFloat(document.getElementById('quoteWeight').value),
            service_type: document.getElementById('quoteService').value,
            dimensions: document.getElementById('quoteDimensions').value
        };

        try {
            const result = await post('/quote', data);
            document.getElementById('estimatedCost').textContent = `$${result.estimated_cost.toFixed(2)}`;
            document.getElementById('quoteDetails').textContent = result.details;
            document.getElementById('quoteResult').style.display = 'block';
        } catch (error) {
            alert('Error calculating quote: ' + error.message);
        }
    });
}

document.addEventListener('DOMContentLoaded', calculateQuote);
