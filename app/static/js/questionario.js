function validateForm() {
    // Detectar el formulario activo (puede ser coffeeForm o citricosForm)
    const form = document.querySelector('form'); // Selecciona el primer formulario en la página
    const inputs = form.querySelectorAll('input[required], select[required]');
    
    for (const input of inputs) {
        if (input.value.trim() === '') {
            if (input.type === 'text') {
                input.value = '0'; // Asignar 0 si el campo está vacío
            } else {
                alert(`Por favor, complete el campo: ${input.previousElementSibling.innerText}`);
                input.focus();
                return false;
            }
        }
    }
    return true;
}

function toggleOtherInput() {
    const q11 = document.getElementById('q11'); // Cambiado para que funcione con citricos_form.html
    const otherInput = document.getElementById('otherInput');
    const selectedOptions = Array.from(q11.selectedOptions).map(option => option.value);

    // Mostrar el campo de texto si "otro" está seleccionado
    if (selectedOptions.includes('otro')) {
        otherInput.style.display = 'block';
        otherInput.required = true; // Hacer que el campo sea obligatorio si se selecciona "Otro"
    } else {
        otherInput.style.display = 'none';
        otherInput.required = false; // Quitar la obligatoriedad si no está seleccionado
        otherInput.value = ''; // Limpiar el valor del campo
    }
}

function formatNumberInput(input) {
    const value = input.value.replace(/[^\d]/g, '');
    input.value = new Intl.NumberFormat('es-MX').format(value);
}
