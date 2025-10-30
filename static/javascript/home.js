var submitForm = document.getElementById("search-form");
var textBox = document.getElementById("search-box");

$(function (){
    $("#search-box").autocomplete({
        source: "/api/food/search-for-foods/",
        minLength: 0, // 2 characters,
        select: handleFormSubmit
    });

    textBox.addEventListener("focus", function(e){
        $("#search-box").autocomplete("search", textBox.value);
    });
});

// has to be async because we use await. doesn't return immediately 
async function handleFormSubmit(e, ui){
    e.preventDefault();
    $("#search-box").autocomplete("close"); // Close the autocomplete dropdown
    
    var searchValue = textBox.value;
    if (ui && ui.item && ui.item.value) {
        searchValue = ui.item.value;
    }
    console.log(searchValue);
    var response = await fetch("/api/food/search/" + searchValue);
    console.log(response);

    const result = await response.json();
    console.log(result);
    displaySearchResults(result);
}

function displaySearchResults(results){
    const resultsArea = document.getElementById("search-results");
    const name = document.getElementById("result-name");
    const id = document.getElementById("result-id");
    const description = document.getElementById("result-description");
    const scientific = document.getElementById("result-scientific");
    const nutrients = document.getElementById("result-nutrients");
    const compounds = document.getElementById("result-compounds");

    // grabbing the objects
    name.textContent = results.name;
    id.textContent = results.id;
    description.textContent = results.description;
    scientific.textContent = results.name_scientific;

    nutrients.textContent = "";
    
    results.nutrients.forEach(function(nutrient) {
        var listItem = document.createElement("li");
        listItem.textContent = `${nutrient.name}: ${nutrient.amount}${nutrient.unit}`;
        nutrients.appendChild(listItem);
    });

    compounds.textContent = "";

    results.compounds.forEach(function(compound) {
        var listItem = document.createElement("li");
        listItem.textContent = `${compound.name}: ${compound.amount}${compound.unit}`;
        compounds.appendChild(listItem);
    });

    resultsArea.style.display = "block";
}

submitForm.addEventListener("submit", handleFormSubmit); 

const form = document.getElementById('search-form');
function checkSubmit(e) {
   if(e && e.keyCode == 13) {
    $("#search-box").autocomplete("close");
    textBox.style.display = "none";
    document.forms[0].submit();
   }
};


const nav = document.querySelector('.navbar');
  const header = document.getElementsByClassName('welcome-title');

  window.addEventListener('scroll', function () {
    if (window.scrollY > header) {
        nav.classList.add('scrolled');
    }
    else {
        nav.classList.remove('scrolled')
    };
  });
