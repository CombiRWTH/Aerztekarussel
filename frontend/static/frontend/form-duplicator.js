document.addEventListener("DOMContentLoaded", function() {
    function handleDuplication(event) {
        event.preventDefault();
        const button = this;
        const sectionClass = button.getAttribute('data-section');
        const section = button.closest('fieldset').querySelector('.' + sectionClass);

        if (!section) {
            console.error('Element with class "' + sectionClass + '" not found.');
            return;
        }

        const newSection = section.cloneNode(true); // Clones the entire section

        // Add the ‘duplicated’ class to the new section
        newSection.classList.add('duplicated');

        // Remove existing ‘duplicated’ sections within the new section
        const innerDuplicatedSections = newSection.querySelectorAll('.duplicated');
        innerDuplicatedSections.forEach(innerSection => {
            innerSection.classList.remove('duplicated');
        });

        // Add event listeners to the new duplicate and remove buttons
        const duplicatedButtons = newSection.querySelectorAll("[data-action='duplicate']");
        duplicatedButtons.forEach(button => {
            button.addEventListener('click', handleDuplication);
        });

        const removeButtons = newSection.querySelectorAll("[data-action='remove']");
        removeButtons.forEach(button => {
            button.addEventListener('click', handleRemoval);
        });

        // Insert the new section after the current section
        section.parentNode.insertBefore(newSection, section.nextSibling);
    }

    function handleRemoval(event) {
        event.preventDefault();
        const button = this;
        const sectionClass = button.getAttribute('data-section');
        const section = button.closest('fieldset').querySelector('.' + sectionClass + '.duplicated');

        if (section) {
            section.remove();
        }
    }

    const duplicationButtons = document.querySelectorAll("[data-action='duplicate']");
    duplicationButtons.forEach(button => {
        button.addEventListener('click', handleDuplication);
    });

    const removeButtons = document.querySelectorAll("[data-action='remove']");
    removeButtons.forEach(button => {
        button.addEventListener('click', handleRemoval);
    });
});
