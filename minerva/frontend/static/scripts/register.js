function verifyForm() {
    let form = document.forms["register"]

    let valid = true;
    valid = setValidation(form["email"], 'Invalid email', validateEmail(form["email"].value)) && valid;
    valid = setValidation(form["password"], 'Password cannot be empty', form["password"].value !== '') && valid;
    valid = setValidation(form["confirm"], 'Passwords must match', form["password"].value === form["confirm"].value) && valid;
    valid = setValidation(form["address"], 'Address cannot be empty', form["address"].value !== '') && valid;
    valid = setValidation(form["zipCode"], 'Zip code cannot be empty', form["zipCode"].value !== '') && valid;
    valid = setValidation(form["cell"], 'Phone number must be valid', validatePhone(form["cell"].value)) && valid;

    return valid;
}

function validateEmail(email) {
    var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
}

function validatePhone(phone) {
    var re = /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/im;
    return re.test(phone);
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