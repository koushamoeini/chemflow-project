// Universal Autocomplete Class - Works for customers, products, and any future models
class UniversalAutocomplete {
    constructor(options) {
        // Required options
        this.triggerInputs = options.triggerInputs; // Inputs that trigger search
        this.updateInputs = options.updateInputs;   // Inputs to update when item selected
        this.resultsContainer = options.resultsContainer;
        this.url = options.url;
        
        // Optional customizations
        this.displayTemplate = options.displayTemplate || this.defaultDisplayTemplate;
        this.minQueryLength = options.minQueryLength || 2;
        this.loadingText = options.loadingText || 'در حال جستجو...';
        
        this.currentFocus = -1;
        this.currentItems = [];
        
        if (this.triggerInputs.length > 0 && this.resultsContainer) {
            this.init();
        } else {
            console.error('UniversalAutocomplete: Missing required elements', {
                triggerInputs: this.triggerInputs.length,
                resultsContainer: !!this.resultsContainer
            });
        }
    }

    init() {
        // Attach event listeners to all trigger inputs
        this.triggerInputs.forEach(input => {
            input.addEventListener('input', this.handleInput.bind(this));
            input.addEventListener('focus', this.handleInput.bind(this));
        });
        
        // Keyboard navigation on first trigger input
        if (this.triggerInputs[0]) {
            this.triggerInputs[0].addEventListener('keydown', this.handleKeydown.bind(this));
        }
        
        document.addEventListener('click', this.handleClickOutside.bind(this));
    }

    handleInput(e) {
        const query = e.target.value.trim();
        
        if (query.length < this.minQueryLength) {
            this.hideResults();
            return;
        }

        this.showLoading();
        this.fetchData(query);
    }

    async fetchData(query) {
        try {
            const response = await fetch(`${this.url}?q=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            this.showResults(data);
        } catch (error) {
            console.error('UniversalAutocomplete - Error fetching data:', error);
            this.showError('خطا در دریافت اطلاعات');
        }
    }

    showResults(items) {
        if (!this.resultsContainer) return;
        
        this.resultsContainer.innerHTML = '';
        this.currentItems = items;
        
        if (items.length === 0) {
            this.showNoResults();
            return;
        }

        items.forEach((item, index) => {
            const itemElement = document.createElement('div');
            itemElement.className = 'autocomplete-item';
            itemElement.innerHTML = this.displayTemplate(item);
            itemElement.dataset.itemIndex = index;
            
            itemElement.addEventListener('click', () => {
                this.selectItem(item);
            });
            
            itemElement.addEventListener('mouseenter', () => {
                this.setActiveItem(index);
            });
            
            this.resultsContainer.appendChild(itemElement);
        });
        
        this.showResultsContainer();
        this.currentFocus = -1;
    }

    defaultDisplayTemplate(item) {
        // Default template that works for both customers and products
        if (item.code && item.name && item.phone) {
            // Customer template
            return `
                <div><strong>${item.code || 'بدون کد'}</strong></div>
                <div>${item.name}</div>
                <div class="small text-muted">${item.phone}</div>
            `;
        } else if (item.code && item.name) {
            // Product template
            return `
                <div><strong>${item.code}</strong></div>
                <div>${item.name}</div>
            `;
        } else {
            // Fallback template
            return `<div>${item.name || item.text || item.value}</div>`;
        }
    }

    showLoading() {
        if (!this.resultsContainer) return;
        
        this.resultsContainer.innerHTML = `<div class="autocomplete-loading">${this.loadingText}</div>`;
        this.showResultsContainer();
    }

    showNoResults() {
        if (!this.resultsContainer) return;
        
        this.resultsContainer.innerHTML = '<div class="autocomplete-loading">نتیجه‌ای یافت نشد</div>';
        this.showResultsContainer();
    }

    showError(message) {
        if (!this.resultsContainer) return;
        
        this.resultsContainer.innerHTML = `<div class="autocomplete-error">${message}</div>`;
        this.showResultsContainer();
    }

    showResultsContainer() {
        if (this.resultsContainer) {
            this.resultsContainer.style.display = 'block';
        }
    }

    hideResults() {
        if (this.resultsContainer) {
            this.resultsContainer.style.display = 'none';
        }
        this.currentFocus = -1;
        this.currentItems = [];
    }

    selectItem(item) {
        // Update all specified input fields
        this.updateInputs.forEach(inputConfig => {
            const input = inputConfig.element;
            const field = inputConfig.field;
            
            if (input && item[field] !== undefined) {
                input.value = item[field];
            }
        });
        
        this.hideResults();
    }

    handleKeydown(e) {
        if (!this.resultsContainer || this.resultsContainer.style.display === 'none') {
            return;
        }
        
        const items = this.resultsContainer.getElementsByClassName('autocomplete-item');
        
        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.currentFocus = Math.min(this.currentFocus + 1, items.length - 1);
                this.setActiveItem(this.currentFocus);
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                this.currentFocus = Math.max(this.currentFocus - 1, -1);
                this.setActiveItem(this.currentFocus);
                break;
                
            case 'Enter':
                if (this.currentFocus > -1 && items[this.currentFocus]) {
                    e.preventDefault();
                    const itemIndex = items[this.currentFocus].dataset.itemIndex;
                    if (this.currentItems[itemIndex]) {
                        this.selectItem(this.currentItems[itemIndex]);
                    }
                }
                break;
                
            case 'Escape':
                e.preventDefault();
                this.hideResults();
                break;
                
            case 'Tab':
                this.hideResults();
                break;
        }
    }

    setActiveItem(index) {
        const items = this.resultsContainer.getElementsByClassName('autocomplete-item');
        
        for (let i = 0; i < items.length; i++) {
            items[i].classList.toggle('autocomplete-active', i === index);
        }
        
        this.currentFocus = index;
    }

    handleClickOutside(e) {
        if (!this.resultsContainer) return;
        
        const isClickInside = this.triggerInputs.some(input => input.contains(e.target)) || 
                             this.resultsContainer.contains(e.target);
        
        if (!isClickInside) {
            this.hideResults();
        }
    }
}

// Helper function to initialize autocomplete for a specific row
function initializeRowAutocomplete(row, options) {
    const triggerInputs = options.triggerSelectors.map(selector => row.querySelector(selector));
    const updateInputs = options.updateSelectors.map(selector => ({
        element: row.querySelector(selector),
        field: selector.dataset?.autocompleteField || 'name' // Default field
    }));
    
    const resultsContainer = row.querySelector(options.resultsSelector);
    
    // Filter out null elements
    const validTriggerInputs = triggerInputs.filter(input => input !== null);
    const validUpdateInputs = updateInputs.filter(config => config.element !== null);
    
    if (validTriggerInputs.length > 0 && resultsContainer) {
        return new UniversalAutocomplete({
            triggerInputs: validTriggerInputs,
            updateInputs: validUpdateInputs,
            resultsContainer: resultsContainer,
            url: options.url,
            displayTemplate: options.displayTemplate
        });
    }
    
    return null;
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UniversalAutocomplete, initializeRowAutocomplete };
}