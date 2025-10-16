document.addEventListener("DOMContentLoaded", function () {
    function cleanupSelectPlaceholders(contextElement) {
        const allSelects = contextElement.querySelectorAll("select");
        allSelects.forEach(sel => {
            if (sel.options.length > 0 && sel.options[0].value === "") {
                sel.options[0].text = "";
            }
        });
    }
    document.querySelectorAll("select").forEach(sel => {
        if (sel.options.length > 0 && sel.options[0].value === "") {
            sel.options[0].text = "";
        }
    });
    cleanupSelectPlaceholders(document.body);

    const addItemBtn = document.getElementById("add-item-btn");
    const formContainer = document.getElementById("form-container");
    const emptyFormTemplate = document.getElementById("empty-form");
    const totalFormsInput = document.querySelector('input[name$="-TOTAL_FORMS"]');

    if (addItemBtn) {
        addItemBtn.addEventListener("click", function (e) {
            e.preventDefault();

            if (!totalFormsInput || !emptyFormTemplate) {
                console.error("Required elements for adding a new form are missing!");
                return;
            }

            let currentFormCount = parseInt(totalFormsInput.value, 10);

            let newForm = emptyFormTemplate.cloneNode(true);
            newForm.removeAttribute("id");
            newForm.innerHTML = newForm.innerHTML.replace(/__prefix__/g, currentFormCount);

            formContainer.appendChild(newForm);
            totalFormsInput.value = currentFormCount + 1;

            cleanupSelectPlaceholders(newForm);
        });
    }
});