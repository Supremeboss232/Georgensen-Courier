/**
 * Quote Calculator for Canadian Global Logistics
 * Handles pricing, currency conversion, and zone-based calculations
 */

class CanadianQuoteCalculator {
    constructor() {
        this.exchangeRate = 1.35;  // CAD to USD (will be fetched in production)
        this.selectedCurrency = localStorage.getItem('appCurrency') || 'CAD';
        this.currentLanguage = localStorage.getItem('appLanguage') || 'en';
        this.currentQuoteData = null;  // Store last quote for currency refresh
        this.init();
    }

    init() {
        const form = document.getElementById('quoteFormComponent');
        if (form) {
            form.addEventListener('submit', (e) => this.handleQuoteSubmit(e));
        }

        // Listen for currency changes
        window.addEventListener('currencyChanged', (e) => {
            this.selectedCurrency = e.detail.currency;
            localStorage.setItem('appCurrency', this.selectedCurrency);
            // Refresh quote display if one exists
            if (this.currentQuoteData) {
                this.displayQuote(this.currentQuoteData);
            }
        });

        // Listen for language changes
        window.addEventListener('languageChanged', (e) => {
            this.currentLanguage = e.detail.language;
        });
    }

    async handleQuoteSubmit(event) {
        event.preventDefault();

        const form = event.target;
        const formData = new FormData(form);

        // Validate postal codes
        const pickupZip = formData.get('pickupZip');
        const deliveryZip = formData.get('deliveryZip');
        
        if (!this.validatePostalCode(pickupZip, formData.get('originCountry'))) {
            alert('Invalid pickup postal code format');
            return;
        }

        if (!this.validatePostalCode(deliveryZip, formData.get('destinationCountry'))) {
            alert('Invalid delivery postal code format');
            return;
        }

        // Build request payload
        const payload = {
            origin_postal: pickupZip,
            destination_postal: deliveryZip,
            origin_country: formData.get('originCountry') || 'CA',
            destination_country: formData.get('destinationCountry') || 'CA',
            weight_kg: parseFloat(formData.get('weight')),
            weight_unit: formData.get('weight') ? 'kg' : 'lbs',
            service_type: formData.get('serviceType'),
            item_type: formData.get('itemType'),
            distance_km: 100,  // Will be calculated by backend from postal codes
        };

        // Handle weight conversion if needed
        if (formData.get('quoteWeightUnit') === 'lbs') {
            payload.weight_kg = payload.weight_kg / 2.20462;  // Convert lbs to kg
            payload.weight_unit = 'lbs';
        }

        try {
            const response = await fetch('/api/v1/quotes/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`Quote calculation failed: ${response.statusText}`);
            }

            const quoteData = await response.json();
            this.displayQuote(quoteData);

        } catch (error) {
            console.error('Quote error:', error);
            alert('Failed to calculate quote. Please try again.');
        }
    }

    validatePostalCode(code, country) {
        if (!code) return false;

        const canadianFormat = /^[A-Z]\d[A-Z]\s?\d[A-Z]\d$/i;
        const usFormat = /^\d{5}(-\d{4})?$/;

        if (country === 'CA') {
            return canadianFormat.test(code);
        } else if (country === 'US') {
            return usFormat.test(code);
        }

        return true;
    }

    displayQuote(quoteData) {
        // Store for currency refresh
        this.currentQuoteData = quoteData;

        const resultDiv = document.getElementById('quoteResult') || 
                         document.getElementById('quoteResultContainer');
        if (!resultDiv) return;

        // Show customs warning if international
        const customsWarning = document.getElementById('customsWarning');
        if (customsWarning) {
            if (quoteData.is_international) {
                customsWarning.style.display = 'block';
            } else {
                customsWarning.style.display = 'none';
            }
        }

        // Get display functions
        const displayAmount = this.selectedCurrency === 'USD' 
            ? (price) => (price / this.exchangeRate).toFixed(2)
            : (price) => price.toFixed(2);

        const currency = this.selectedCurrency;
        const currencySymbol = currency === 'USD' ? 'US$' : '$';
        const currencyCode = ` ${currency}`;

        // Update pricing components
        if (document.getElementById('quoteBaseRate')) {
            document.getElementById('quoteBaseRate').textContent = 
                `${currencySymbol}${displayAmount(quoteData.base_fare)}`;
        }

        if (document.getElementById('quoteWeightCharge')) {
            document.getElementById('quoteWeightCharge').textContent = 
                `${currencySymbol}${displayAmount(quoteData.weight_charge)}`;
        }

        if (document.getElementById('quoteFuelCharge')) {
            document.getElementById('quoteFuelCharge').textContent = 
                `${currencySymbol}${displayAmount(quoteData.fuel_surcharge)}`;
        }

        if (document.getElementById('quoteDistanceCharge')) {
            document.getElementById('quoteDistanceCharge').textContent = 
                `${currencySymbol}${displayAmount(quoteData.distance_charge)}`;
        }

        if (document.getElementById('quoteTaxes')) {
            document.getElementById('quoteTaxes').textContent = 
                `${currencySymbol}${displayAmount(quoteData.tax_amount)}`;
        }

        // Update tax label based on jurisdiction
        const taxLabel = document.getElementById('taxLabel');
        if (taxLabel) {
            const jurisdiction = quoteData.tax_jurisdiction;
            let taxDesc = 'Tax';
            
            if (jurisdiction.includes('HST')) {
                taxDesc = 'HST';
            } else if (jurisdiction === 'QC') {
                taxDesc = 'GST + PST';
            } else if (jurisdiction === 'AB') {
                taxDesc = 'GST';
            }
            
            taxLabel.textContent = `${taxDesc}:`;
        }

        // Update total
        if (document.getElementById('estimatedCost')) {
            document.getElementById('estimatedCost').textContent = 
                `${currencySymbol}${displayAmount(quoteData.total_price)}`;
        }

        // Update route info
        const originProvince = this.getProvinceFromPostal(quoteData.origin_postal);
        const destProvince = this.getProvinceFromPostal(quoteData.destination_postal);

        if (document.getElementById('quoteRoute')) {
            document.getElementById('quoteRoute').innerHTML = 
                `<span style="font-weight: 600; color: var(--primary-color);">${originProvince}</span> → <span style="font-weight: 600; color: var(--secondary-color);">${destProvince}</span>`;
        }

        if (document.getElementById('quoteZone')) {
            document.getElementById('quoteZone').textContent = 
                this.formatZone(quoteData.zone);
        }

        if (document.getElementById('quoteTaxRate')) {
            document.getElementById('quoteTaxRate').textContent = 
                `${quoteData.tax_rate}%`;
        }

        // Add customs fee info if international
        if (quoteData.is_international && document.getElementById('quoteCustomsFee')) {
            document.getElementById('quoteCustomsFee').innerHTML = 
                `<p style="margin: 5px 0;"><strong>Customs Fee:</strong> ${currencySymbol}${displayAmount(quoteData.customs_fee)}</p>`;
            document.getElementById('quoteCustomsFee').style.display = 'block';
        }

        // Update quote details text
        const estDays = quoteData.estimated_delivery_days || 2;
        const notes = quoteData.notes ? `<br><small style="color: #666;">ℹ ${quoteData.notes}</small>` : '';
        
        if (document.getElementById('quoteDetails')) {
            document.getElementById('quoteDetails').innerHTML = 
                `<i class="fas fa-check-circle" style="color: var(--success-color); margin-right: 8px;"></i>` +
                `Estimated delivery: <strong>${estDays} business day${estDays !== 1 ? 's' : ''}</strong> • ` +
                `Quote in <strong>${currency}</strong>${notes}`;
        }

        // Show result
        if (resultDiv) {
            resultDiv.style.display = 'block';
            resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    getProvinceFromPostal(postal) {
        if (!postal) return 'Unknown';

        const provinceMap = {
            'A': 'NL', 'B': 'NS', 'C': 'PE', 'E': 'NB',
            'G': 'QC', 'H': 'QC', 'J': 'QC',
            'K': 'ON', 'L': 'ON', 'M': 'ON', 'N': 'ON', 'P': 'ON',
            'R': 'MB',
            'S': 'SK',
            'T': 'AB',
            'V': 'BC',
        };

        return provinceMap[postal.charAt(0).toUpperCase()] || 'CA';
    }

    formatZone(zone) {
        const zones = {
            'zone_1': 'Zone 1 - Intra-City',
            'zone_2': 'Zone 2 - Regional',
            'zone_3': 'Zone 3 - Continental',
            'zone_4': 'Zone 4 - Air Freight',
            'zone_5': 'Zone 5 - Ocean Freight',
        };

        return zones[zone] || zone;
    }

    convertCurrency(amount, fromCurrency, toCurrency) {
        if (fromCurrency === toCurrency) {
            return amount;
        }

        if (fromCurrency === 'CAD' && toCurrency === 'USD') {
            return amount / this.exchangeRate;
        } else if (fromCurrency === 'USD' && toCurrency === 'CAD') {
            return amount * this.exchangeRate;
        }

        return amount;
    }
}

// Initialize quote calculator when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.quoteCalculator = new CanadianQuoteCalculator();
    });
} else {
    window.quoteCalculator = new CanadianQuoteCalculator();
}
