document.addEventListener('DOMContentLoaded', () => {
    const addButton = document.getElementById('add-item-btn');
    const tableBody = document.getElementById('form-container'); 
    const emptyFormTemplate = document.getElementById('empty-form-template'); 
    const totalFormsInput = document.querySelector('input[name$="TOTAL_FORMS"]');
    const form = document.getElementById('overtime-form');
    const submitButton = document.getElementById('submit-button');
    
    if (!addButton || !tableBody || !emptyFormTemplate || !totalFormsInput || !form) {
        console.error("One or more required formset elements are missing.");
        return;
    }

    const prefix = totalFormsInput.name.replace('-TOTAL_FORMS', '');

    function cleanEmptyLabels(container) {
        container.querySelectorAll("select").forEach(sel => {
            if (sel.options.length > 0 && sel.options[0].value === "") {
                sel.options[0].text = "";
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

        cleanEmptyLabels(newRow);
        updateDeleteButtons();
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

    if (form) {
        form.addEventListener('submit', () => {
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = 'در حال ثبت...';
            }
        });
    }

    hideDeletedRowsOnLoad(); 
    
    if (tableBody.querySelectorAll('tr.formset-row:not(.row-hidden)').length === 0) {
       addFormRow();
    } else {
        cleanEmptyLabels(document); 
        updateDeleteButtons(); 
    }
});
