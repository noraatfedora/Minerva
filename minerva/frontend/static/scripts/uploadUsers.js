let index = 0;

function verifyForm() {
    let form = document.forms["register"]

    let valid = true;
    valid = setValidation(form["name"], 'Invalid name', form["name"].value !== '') && valid;
    valid = setValidation(form["address"], 'Address cannot be empty', form["address"].value !== '') && valid;
    valid = setValidation(form["zipCode"], 'Zip code cannot be empty', form["zipCode"].value !== '') && valid;

    for (let i = 0; i < index; i++) {
        if (form[`name${i}`]) {
            valid = setValidation(form[`name${i}`], 'Field cannot be empty', form[`name${i}`].value !== '') && valid;
            valid = setValidation(form[`race${i}`], 'Field cannot be empty', form[`race${i}`].value !== '') && valid;
        }
    }

    valid ? form.submit() : null;
    return false;
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

function addMember() {
    const fields =
    `<div id="household-member-${index}">
        <div class="form-group">
        <input type="text" name="name${index}" id="name${index}" class="form-control"
            placeholder="Name">
        <small>Error message</small>
        </div>
        <div class="form-group">
            <input type="text" name="race${index}" id="race${index}" class="form-control"
                placeholder="Race">
            <small>Error message</small>
        </div>
        <button class="add-remove-button" onclick="event.preventDefault(); removeMember(${index})">–</button>
        <br>
    </div>`;

    document.querySelector("#household-members").insertAdjacentHTML('beforeend', fields);
    index++;
}

function removeMember(toRemove) {
    const select = document.getElementById("household-member-" + toRemove);
    select.parentNode.removeChild(select);
    /*
    if (index > 0) {
        index--;
    }
    */
}