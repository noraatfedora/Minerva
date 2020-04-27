var filterList = [];

function updateFilter(filter) {    
    if(filter != '') {
      document.getElementById("dropdownMenuButton").innerHTML =  filter.substring(0,1).toUpperCase() + "" +  filter.substring(1);
    } else {
      document.getElementById("dropdownMenuButton").innerHTML = "Filter"; 
    }

    if(filter == '') {
        clearAll();
        document.getElementById("filter-text").innerHTML = "All";  
    } else {
        add(filter);
        document.getElementById("filter-text").innerHTML = filterList;  
    }

    
    console.log(filterList);

    filter = filter.toUpperCase();
    let elements = document.getElementsByClassName('item')
    for (let i = 0; i < elements.length; i++) {
      let element = elements[i];
      if (element.getAttribute('category').toUpperCase() != filter && filter != '') {
        element.style.display = 'none';
      } else {
        element.style.display = 'block';
      }
    }
}

function add(filter) { 
    if(filterList.indexOf(filter) == -1 ) {
        filterList.push(filter)
    }
         
}

function remove(filter) { 
    let removeIndex = filterList.indexOf(filter);
    if(removeIndex != null && removeIndex >= 0) {
        filterList.splice(removeIndex,1);
    }
}

function clearAll() {
    filterList = [];
}










