var filterList = [];

function updateFilter(filter) {    
    if(filter != '') {
      document.getElementById("filter-button").innerHTML =  filter.substring(0,1).toUpperCase() + "" +  filter.substring(1);
    } else {
      document.getElementById("filter-button").innerHTML = "Filter"; 
    }
    
    filter = filter.toUpperCase();
    let elements = document.getElementsByClassName('item');
    for (let i = 0; i < elements.length; i++) {
      let element = elements[i];
      if (element.getAttribute('filter').toUpperCase() != filter && filter != '') {
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