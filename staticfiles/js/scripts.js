const input = document.querySelector("#phone1");
const error_msg = document.querySelector("#error_msg");

const ho = window.intlTelInput(input, {
    initialCountry: 'np',
    loadUtils: () =>
        import("https://cdn.jsdelivr.net/npm/intl-tel-input@26.7.6/build/js/utils.js"),
});

document.getElementById("contactform").addEventListener('submit', function (e) {
    if (ho.isValidNumber()) {
        input.value = ho.getNumber();
        error_msg.style.display = 'none';
    } else {
        error_msg.style.display = 'inline';
        e.preventDefault()
    }
})