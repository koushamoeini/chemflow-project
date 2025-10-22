document.addEventListener('DOMContentLoaded', () => {
    const addButton = document.getElementById('add-item-btn');
    const tableBody = document.getElementById('form-container'); 
    const emptyFormTemplate = document.getElementById('empty-form-template'); 
    const totalForms = document.querySelector('input[name$="TOTAL_FORMS"]');
    const prefix = totalForms.name.replace('-TOTAL_FORMS', '');
    const form = document.getElementById('prodreq-form');
    const submitButton = document.getElementById('submit-button');

    function cleanEmptyLabels(container) {
        container.querySelectorAll("select").forEach(sel => {
            if (sel.options.length > 0 && sel.options[0].value === "") {
                sel.options[0].text = "";
            }
        });
    }
    
    cleanEmptyLabels(document);
    
    function hideDeletedRowsOnLoad() {
        tableBody.querySelectorAll('tr.formset-row').forEach(row => {
            const deleteCheckbox = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
            if (deleteCheckbox && deleteCheckbox.checked) {
                row.classList.add('row-hidden');
            }
        });
    }

    hideDeletedRowsOnLoad();
    
    function updateElementIndex(el, index) {
        const idRegex = new RegExp('(' + prefix + '-\\d+|__prefix__)(-[a-zA-Z0-9_]+)');
        const replacement = prefix + '-' + index + '$2';

        if (el.id) {
            el.id = el.id.replace(idRegex, replacement);
        }
        if (el.name) {
            el.name = el.name.replace(idRegex, replacement);
        }
    }
    
    addButton.addEventListener('click', (e) => {
        e.preventDefault();

        let newIndex = parseInt(totalForms.value);
        const newRow = emptyFormTemplate.content.cloneNode(true).querySelector('tr');

        newRow.querySelectorAll('*').forEach(el => {
            updateElementIndex(el, newIndex);
        });

        tableBody.appendChild(newRow);
        totalForms.value = newIndex + 1;

        const deleteCheckbox = newRow.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (deleteCheckbox) {
            deleteCheckbox.checked = false;
        }

        cleanEmptyLabels(newRow);
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
});