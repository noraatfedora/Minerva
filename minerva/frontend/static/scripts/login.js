function verifyForm() {
    let form = document.forms["login"]

    let valid = true;
    valid = setValidation(form["email"], 'Invalid email', validateEmail(form["email"].value)) && valid;
    valid = setValidation(form["password"], 'Password cannot be empty', form["password"].value !== '') && valid;

    return valid;
}

function validateEmail(email) {
    var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
}

function setValidation(input, message, valid) {
	const formControl = input.parentElement;
    const small = formControl.querySelector('small');
    if (!valid) {
        input.className = 'form-control error';
        small.innerText = message;
        small.style.display = "block";
    } else {
        input.className = 'form-control';
        small.style.display = "none";
    }

    return valid;
}