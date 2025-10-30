const submitForm = document.getElementById("search-form");
const textBox = document.getElementById("search-box");
const shoppingListButton = document.getElementById("shopping-list-btn");

let searchResult;
let userAllergies = JSON.parse(localStorage.getItem("userAllergies") || "[]");
let shoppingList = JSON.parse(localStorage.getItem("shoppingList") || "[]");

$(function (){
    // ===== Autocomplete for USDA search =====
    $("#search-box").autocomplete({
        source: async function(request, response) {
            const term = request.term;
            try {
                const res = await fetch(`/api/usda/food/search/?term=${encodeURIComponent(term)}`);
                const data = await res.json();

                const ignoredCompanies = ["Ferrero", "Nestle", "PepsiCo", "Kraft", "General Mills", "Unilever"];
                const formatted = data.map(item => {
                    let brand = item.brandName || item.brandOwner || "";
                    let description = item.label || "";
                    let displayName = (brand && !ignoredCompanies.includes(brand) && !description.toLowerCase().includes(brand.toLowerCase())) 
                                      ? brand + " " + description 
                                      : description;
                    return { label: displayName, value: item.value };
                });
                response(formatted);
            } catch(err) {
                console.error(err);
                response([]);
            }
        },
        minLength: 0,
        select: handleFormSubmit
    });

    // ===== Autocomplete for allergies =====
    $("#allergy-search").autocomplete({
        source: "/api/allergies",
        minLength: 0,
        select: handleAddAllergy
    });

    textBox.addEventListener("focus", () => {
        $("#search-box").autocomplete("search", textBox.value);
    });

    $("#accordion").accordion({
        active: false,
        heightStyle: "content",
        animate: { duration: 400, easing: "swing" },
        collapsible: true
    });
});

// ===== Handle search selection =====
async function handleFormSubmit(e, ui){
    e.preventDefault();
    $("#search-box").autocomplete("close"); 
    if (!ui?.item?.value) return;

    const response = await fetch(`/api/usda/food/${ui.item.value}`);
    const result = await response.json();
    searchResult = result;

    displaySearchResults(result);
    findAlternatives();
}

// ===== Display main search result =====
function displaySearchResults(result){
    const resultsArea = document.getElementById("search-results");
    const nameElem = document.getElementById("result-name");
    const brandElem = document.getElementById("result-brand");
    const ingredientsElem = document.getElementById("result-ingredients");

    const ignoredCompanies = ["Ferrero", "Nestle", "PepsiCo", "Kraft", "General Mills", "Unilever"];
    let brand = result.raw_data?.brandName || result.raw_data?.brandOwner || "";
    let displayName = result.name || "";
    if (brand && !ignoredCompanies.includes(brand) && !displayName.toLowerCase().includes(brand.toLowerCase())) {
        displayName = brand + " " + displayName;
    }

    nameElem.textContent = displayName;
    brandElem.textContent = brand;

    // Ingredients
    ingredientsElem.textContent = "";
    if (result.ingredients && result.ingredients.length > 0) {
        result.ingredients.forEach(ing => {
            const li = document.createElement("li");
            li.textContent = ing;
            ingredientsElem.appendChild(li);
        });
    } else {
        const li = document.createElement("li");
        li.textContent = "N/A";
        ingredientsElem.appendChild(li);
    }

    // Ensure allergens array exists
    if (!result.allergens) result.allergens = [];

    displayAllergyList();
    resultsArea.style.display = "block";
}

// ===== Allergy handling =====
function handleAddAllergy(e, ui){
    e.preventDefault();
    const value = ui?.item?.value || e.target.value;
    if (!value) return;

    if (!userAllergies.includes(value)) {
        userAllergies.push(value);
        localStorage.setItem("userAllergies", JSON.stringify(userAllergies));
        displayAllergyList();
        findAlternatives();
    }
    e.target.value = "";
}

function handleRemoveAllergy(allergen){
    const index = userAllergies.indexOf(allergen);
    if (index > -1) userAllergies.splice(index, 1);
    localStorage.setItem("userAllergies", JSON.stringify(userAllergies));
    displayAllergyList();
    findAlternatives();
}

function isCurrentItemAllergenFree(){
    if (!searchResult.ingredients) return true;

    return !userAllergies.some(allergen => {
        const allergenLower = allergen.toLowerCase();
        // check in allergens field (if exists) OR in ingredient list
        const inAllergens = searchResult.allergens?.some(a => a.toLowerCase() === allergenLower);
        const inIngredients = searchResult.ingredients.some(ing => ing.toLowerCase().includes(allergenLower));
        return inAllergens || inIngredients;
    });
}

function displayAllergyList(){
    const allergensElem = document.getElementById("result-allergens");
    allergensElem.textContent = "";
    
    userAllergies.forEach(allergen => {
        const li = document.createElement("li");
        li.textContent = allergen;

        const allergenLower = allergen.toLowerCase();
        const contains = searchResult.allergens?.some(a => a.toLowerCase() === allergenLower) ||
                         searchResult.ingredients?.some(ing => ing.toLowerCase().includes(allergenLower));

        li.classList.add(contains ? "contains-allergen" : "allergen-free");

        const removeBtn = document.createElement("button");
        removeBtn.textContent = "Remove";
        removeBtn.classList.add("remove-btn");
        removeBtn.addEventListener("click", () => handleRemoveAllergy(allergen));
        li.appendChild(removeBtn);

        allergensElem.appendChild(li);
    });

    shoppingListButton.classList.toggle("hidden", !isCurrentItemAllergenFree());
}


// ===== Shopping list =====
function addToShoppingList(){
    const message = document.getElementById("shopping-list-message");
    if (shoppingList.includes(searchResult.id)){
        message.textContent = "You've already added this item!";
        message.classList.add("error");
    } else {
        shoppingList.push(searchResult.id);
        localStorage.setItem("shoppingList", JSON.stringify(shoppingList));
        message.textContent = "Successfully added to the shopping list!";
    }
    message.classList.remove("hidden");
    setTimeout(() => {
        message.classList.add("hidden");
        message.classList.remove("error");
    }, 4000);
}

// ===== Find alternatives =====
async function findAlternatives() {
    const alternativesContainer = document.querySelector(".find-alternatives");
    alternativesContainer.innerHTML = "<p>Loading alternatives...</p>";

    if (!searchResult || !searchResult.id) {
        alternativesContainer.innerHTML = "<p>No product selected.</p>";
        return;
    }

    const allergies = userAllergies.join(",");
    try {
        const response = await fetch(`/api/usda/food/alternatives/${searchResult.id}?allergies=${encodeURIComponent(allergies)}`);
        let alternatives = await response.json();

        // Filter out items with no ingredients or same as main
        alternatives = alternatives.filter(food => 
            food.ingredients && food.ingredients.length > 0 && food.id !== searchResult.id
        );

        if (alternatives.length === 0) {
            alternativesContainer.innerHTML = "<p>No safe alternatives found.</p>";
            return;
        }

        alternativesContainer.innerHTML = "<h3>Want other options? Here's our suggestions: </h3>";

        const flexContainer = document.createElement("div");
        flexContainer.style.display = "flex";
        flexContainer.style.flexWrap = "wrap";
        flexContainer.style.gap = "16px";
        alternativesContainer.appendChild(flexContainer);

        alternatives.forEach(food => {
            const card = document.createElement("div");
            card.className = "alternative-card";
            card.style.flex = "1 1 250px"; // responsive width

            const badges = food.allergy_safe ? food.allergy_safe.map(a => `<span class="badge">${a}</span>`).join(" ") : "";

            card.innerHTML = `
                <h4>${food.name}</h4>
                <p><em>${food.brand || "No brand"}</em></p>
                <div class="badges">${badges}</div>
                <button type="button" class="toggle-ingredients-btn">Show Ingredients ▼</button>
                <ul class="alt-ingredients" style="display:none; list-style:none; padding-left:0; margin-top:8px;">
                    ${food.ingredients.map(i => `<li>${i}</li>`).join("")}
                </ul>
            `;

            // Toggle ingredients visibility
            const toggleBtn = card.querySelector(".toggle-ingredients-btn");
            const ingredientsList = card.querySelector(".alt-ingredients");
            toggleBtn.addEventListener("click", () => {
                if (ingredientsList.style.display === "none") {
                    ingredientsList.style.display = "block";
                    toggleBtn.textContent = "Hide Ingredients ▲";
                } else {
                    ingredientsList.style.display = "none";
                    toggleBtn.textContent = "Show Ingredients ▼";
                }
            });

            // Click card to update main product
            card.addEventListener("click", (e) => {
                // Prevent click from toggling ingredients button
                if (e.target === toggleBtn) return;

                searchResult = food;
                displaySearchResults(food);
                findAlternatives(); // refresh alternatives for new main product
                document.getElementById("search-results").scrollIntoView({ behavior: "smooth" });
            });

            flexContainer.appendChild(card);
        });
    } catch (err) {
        console.error(err);
        alternativesContainer.innerHTML = "<p>Error fetching alternatives. Please try again.</p>";
    }
}


// ===== Event listeners =====
submitForm.addEventListener("submit", handleFormSubmit); 
shoppingListButton.addEventListener("click", addToShoppingList);
