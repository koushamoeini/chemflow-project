document.addEventListener('DOMContentLoaded', () => {
    const addButton = document.getElementById('add-item-btn');
    const tableBody = document.getElementById('form-container'); 
    
    const emptyFormTemplate = document.getElementById('empty-form-template'); 
    
    const totalForms = document.querySelector('input[name$="TOTAL_FORMS"]');
    const prefix = totalForms.name.replace('-TOTAL_FORMS', '');

    document.querySelectorAll("select").forEach(sel => {
        if (sel.options.length > 0 && sel.options[0].value === "") {
            sel.options[0].text = ""; 
        }
    });
    
    
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
    });
});
