document.addEventListener("DOMContentLoaded", function () {
    
    function cleanupSelectPlaceholders(contextElement) {
        const allSelects = contextElement.querySelectorAll("select");
        allSelects.forEach(sel => {
            if (sel.options.length > 0 && sel.options[0].value === "") {
                sel.options[0].text = "";
            }
        });
    }

    const orderForm = document.getElementById('order-form');
    if (!orderForm) return;

    const addButton = document.getElementById('add-item-btn');
    const tableBody = document.getElementById('form-container'); 
    const emptyFormTemplate = document.getElementById('empty-form-template'); 
    const totalFormsInput = document.querySelector('input[name$="TOTAL_FORMS"]');
    const submitButton = document.getElementById('submit-button');

    if (!addButton || !tableBody || !emptyFormTemplate || !totalFormsInput) {
        console.error("Formset elements (buttons, container, template, or TOTAL_FORMS) are missing!");
        return;
    }

    const prefix = totalFormsInput.name.replace('-TOTAL_FORMS', '');
    
    const customerAutocompleteUrl = orderForm.dataset.customerAutocompleteUrl;
    const productAutocompleteUrl = orderForm.dataset.productAutocompleteUrl;
    const customerNameId = orderForm.dataset.customerNameId;
    const customerCodeId = orderForm.dataset.customerCodeId;
    const customerPhoneId = orderForm.dataset.customerPhoneId;
    const recipientAddressId = orderForm.dataset.recipientAddressId;

    const customerAutocomplete = new UniversalAutocomplete({
        triggerInputs: [
            document.getElementById(customerNameId),
            document.getElementById(customerCodeId)
        ],
        updateInputs: [
            { element: document.getElementById(customerNameId), field: 'name' },
            { element: document.getElementById(customerCodeId), field: 'code' },
            { element: document.getElementById(customerPhoneId), field: 'phone' },
            { element: document.getElementById(recipientAddressId), field: 'address' }
        ],
        resultsContainer: document.getElementById('autocomplete-results'),
        url: customerAutocompleteUrl,
        displayTemplate: (customer) => `
            <div><strong>${customer.code || 'بدون کد'}</strong></div>
            <div>${customer.name}</div>
            <div class="small text-muted">${customer.phone}</div>
        `
    });

    function initializeProductAutocomplete(contextRow) {
        const rowsToScan = contextRow ? [contextRow] : document.querySelectorAll('.item-form');
        
        rowsToScan.forEach(row => {
            const productNameInput = row.querySelector('input[name$="-product_name"]');
            const productCodeInput = row.querySelector('input[name$="-product_code"]');
            const resultsContainer = row.querySelector('.product-autocomplete-results');

            if (productNameInput && productCodeInput && resultsContainer) {
                if(productNameInput.dataset.autocompleteInitialized) return;
                productNameInput.dataset.autocompleteInitialized = 'true';
                
                new UniversalAutocomplete({
                    triggerInputs: [productNameInput, productCodeInput],
                    updateInputs: [
                        { element: productNameInput, field: 'name' },
                        { element: productCodeInput, field: 'code' }
                    ],
                    resultsContainer: resultsContainer,
                    url: productAutocompleteUrl,
                    displayTemplate: (product) => `
                        <div><strong>${product.code}</strong></div>
                        <div>${product.name}</div>
                    `
                });
            }
        });
    }

    function updateDeleteButtons() {
        const visibleRows = tableBody.querySelectorAll('tr.formset-row:not(.row-hidden)');
        visibleRows.forEach((row, index) => {
            const deleteButton = row.querySelector('.delete-row-btn');
            if (deleteButton) {
                deleteButton.style.display = visibleRows.length > 1 ? 'flex' : 'none';
            }
        });
    }
    
    function hideDeletedRowsOnLoad() {
        tableBody.querySelectorAll('tr.formset-row').forEach(row => {
            const deleteCheckbox = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
            if (deleteCheckbox && deleteCheckbox.checked) {
                row.classList.add('row-hidden');
            }
        });
    }
    
    function updateElementIndex(el, index) {
        const idRegex = new RegExp(prefix + '-\\d+-');
        const nameRegex = new RegExp(prefix + '-\\d+-');
        const newIdPrefix = prefix + '-' + index + '-';
        const newNamePrefix = prefix + '-' + index + '-';

        if (el.id && el.id.startsWith(prefix + '-')) {
             el.id = el.id.replace(idRegex, newIdPrefix);
        }
         if (el.name && el.name.startsWith(prefix + '-')) {
             el.name = el.name.replace(nameRegex, newNamePrefix);
        }
        
        const prefixPlaceholderId = new RegExp('__prefix__');
        const prefixPlaceholderName = new RegExp('__prefix__');
         if (el.id && el.id.includes('__prefix__')) {
             el.id = el.id.replace(prefixPlaceholderId, index);
         }
         if (el.name && el.name.includes('__prefix__')) {
             el.name = el.name.replace(prefixPlaceholderName, index);
         }
    }

    function addFormRow() {
        let newIndex = parseInt(totalFormsInput.value);
        const newRow = emptyFormTemplate.content.cloneNode(true).querySelector('tr');

        newRow.querySelectorAll('input, select, textarea, button, div[id*="__prefix__"]').forEach(el => {
            updateElementIndex(el, newIndex);
        });

        tableBody.appendChild(newRow);
        totalFormsInput.value = newIndex + 1;

        const hiddenDeleteCheckbox = newRow.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (hiddenDeleteCheckbox) {
            hiddenDeleteCheckbox.checked = false;
        }

        cleanupSelectPlaceholders(newRow);
        updateDeleteButtons();
        
        setTimeout(() => {
            initializeProductAutocomplete(newRow);
        }, 100);
    }
    
    addButton.addEventListener('click', (e) => {
        e.preventDefault();
        addFormRow();
    });

    tableBody.addEventListener('click', (e) => {
        if (e.target && e.target.classList.contains('delete-row-btn')) {
            e.preventDefault();
            
            const row = e.target.closest('tr.formset-row');
            if (!row) return;

            const deleteCheckbox = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
            
            if (deleteCheckbox) {
                deleteCheckbox.checked = true;
                row.classList.add('row-hidden');
                updateDeleteButtons(); 
            }
        }
    });

    orderForm.addEventListener('submit', () => {
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'در حال ثبت...';
        }
    });

    cleanupSelectPlaceholders(document.body);
    initializeProductAutocomplete(null); 
    hideDeletedRowsOnLoad(); 
    
    if (tableBody.querySelectorAll('tr.formset-row:not(.row-hidden)').length === 0) {
       addFormRow();
    } else {
        updateDeleteButtons(); 
    }
});

