/**
 * Bilingual Support for Georgensen Courier (EN/FR)
 * Handles language switching and translation of DOM elements
 */

class BilingualManager {
    constructor() {
        this.currentLanguage = localStorage.getItem('appLanguage') || 'en';
        this.supportedLanguages = ['en', 'fr'];
        this.init();
    }

    init() {
        // Set initial language
        this.setLanguage(this.currentLanguage);
        
        // Setup language toggle listeners
        document.querySelectorAll('.lang-toggle-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const lang = btn.dataset.lang || btn.textContent.toLowerCase();
                this.setLanguage(lang);
            });
        });
    }

    setLanguage(lang) {
        if (!this.supportedLanguages.includes(lang)) {
            lang = 'en';
        }

        this.currentLanguage = lang;
        localStorage.setItem('appLanguage', lang);
        document.documentElement.lang = lang;
        window.currentLanguage = lang;

        // Update all translatable elements
        this.updatePageTranslations(lang);
        
        // Update language toggle button states
        this.updateLanguageButtonStates(lang);
    }

    updatePageTranslations(lang) {
        // Find all elements with data-en and data-fr attributes
        document.querySelectorAll('[data-en][data-fr]').forEach(element => {
            const text = element.getAttribute(`data-${lang}`);
            if (text) {
                // Update text content while preserving child elements
                if (element.children.length === 0) {
                    element.textContent = text;
                } else {
                    // For elements with children, update only the text nodes
                    element.childNodes.forEach(node => {
                        if (node.nodeType === Node.TEXT_NODE) {
                            node.textContent = text;
                        }
                    });
                }
            }
        });

        // Update form labels and placeholders
        this.updateFormElements(lang);
    }

    updateFormElements(lang) {
        const formLabels = {
            'en': {
                'quoteOriginCountry': 'Origin Country',
                'quoteDestinationCountry': 'Destination Country',
                'quotePickupZip': 'Pickup Postal Code',
                'quotePickupCity': 'Pickup City/Town',
                'quotePickupProvince': 'Pickup Province/State',
                'quoteDeliveryZip': 'Delivery Postal Code',
                'quoteDeliveryCity': 'Delivery City/Town',
                'quoteDeliveryProvince': 'Delivery Province/State',
                'quoteWeight': 'Package Weight',
                'quoteService': 'Service Type',
                'quoteItemType': 'Item Type (for customs classification)',
            },
            'fr': {
                'quoteOriginCountry': 'Pays d\'Origine',
                'quoteDestinationCountry': 'Pays de Destination',
                'quotePickupZip': 'Code Postal de Départ',
                'quotePickupCity': 'Ville/Municipalité de Départ',
                'quotePickupProvince': 'Province/État de Départ',
                'quoteDeliveryZip': 'Code Postal de Livraison',
                'quoteDeliveryCity': 'Ville/Municipalité de Livraison',
                'quoteDeliveryProvince': 'Province/État de Livraison',
                'quoteWeight': 'Poids du Colis',
                'quoteService': 'Type de Service',
                'quoteItemType': 'Type d\'Article (pour classification douanière)',
            }
        };

        const labels = formLabels[lang] || formLabels['en'];
        Object.entries(labels).forEach(([id, text]) => {
            const label = document.querySelector(`label[for="${id}"]`);
            if (label) {
                label.textContent = text;
            }
        });
    }

    updateLanguageButtonStates(lang) {
        document.querySelectorAll('.lang-toggle-btn').forEach(btn => {
            const btnLang = btn.textContent.toLowerCase();
            if (btnLang === lang) {
                btn.style.color = 'white';
                btn.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
            } else {
                btn.style.color = 'rgba(255, 255, 255, 0.6)';
                btn.style.backgroundColor = 'transparent';
            }
        });
    }

    getCurrentLanguage() {
        return this.currentLanguage;
    }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.bilingualManager = new BilingualManager();
    });
} else {
    window.bilingualManager = new BilingualManager();
}

// Global function for language switching
function setLanguage(lang) {
    if (window.bilingualManager) {
        window.bilingualManager.setLanguage(lang);
    }
}
