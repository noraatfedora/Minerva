let index = 0;

function verifyForm() {
    let form = document.forms["register"]

    let valid = true;
    valid = setValidation(form["name"], 'Invalid name', form["name"].value !== '') && valid;
    valid = setValidation(form["birthday"], 'Invalid birthday', form["birthday"].value !== '') && valid;
    valid = setValidation(form["email"], 'Invalid email', validateEmail(form["email"].value)) && valid;
    valid = setValidation(form["password"], 'Password cannot be empty', form["password"].value !== '') && valid;
    valid = setValidation(form["confirm"], 'Passwords must match', form["password"].value === form["confirm"].value && form["confirm"].value !== '') && valid;
    valid = setValidation(form["address"], 'Address cannot be empty', form["address"].value !== '') && valid;
    valid = setValidation(form["zipCode"], 'Zip code cannot be empty', form["zipCode"].value !== '') && valid;
    valid = setValidation(form["cell"], 'Phone number must be valid', validatePhone(form["cell"].value)) && valid;

    for (let i = 0; i < index; i++) {
        console.log(form[`name${i}`].value);
        console.log(form[`race${i}`].value);
        valid = setValidation(form[`name${i}`], 'Field cannot be empty', form[`name${i}`].value !== '') && valid;
        valid = setValidation(form[`race${i}`], 'Field cannot be empty', form[`race${i}`].value !== '') && valid;
    }
    
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

function initializeItems(items) {
    console.log(items);
    items.forEach((item) => addItem(item));
}

function addItem(item) {
    const fields =
    `<div id="item-field-${index}">
        <div class="form-group">
        <input type="text" name="name${index}" id="name${index}" class="form-control"
            placeholder="Item Name" default="${item}">
        <small>Error message</small>
        </div>
        <button class="add-remove-button" onclick="event.preventDefault(); removeItem(${index})">–</button>
        <br>
    </div>`;

    document.querySelector("#item-fields").insertAdjacentHTML('beforeend', fields);
    index++;
}

function removeItem(toRemove) {
    const select = document.getElementById("item-field-" + toRemove);
    select.parentNode.removeChild(select);
    /*
    if (index > 0) {
        index--;
    }
    */
}