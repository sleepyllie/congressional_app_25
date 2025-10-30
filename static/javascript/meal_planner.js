const submitButton = document.getElementById("submit-btn");
const allergyInput = document.getElementById("allergy-search");
const cuisineInput = document.getElementById("cuisine");
const categoryInput = document.getElementById("category");

var userAllergies = JSON.parse(localStorage.getItem("userAllergies") || "[]");

$(function (){
    $("#allergy-search").autocomplete({
        source: "/api/allergies",
        minLength: 0,
        select: handleAddAllergy
    });

    $("#category").autocomplete({
        source: "api/meal-planner/categories",
        minLength: 0
    });

    $("#cuisine").autocomplete({
        source: "api/meal-planner/cuisines",
        minLength: 0
    });
});

async function handleMealPlannerRequest(){
    let allergies = userAllergies.join(',');
    let cuisine = cuisineInput.value;
    let category = categoryInput.value;

    const response = await fetch("/api/meal-planner?allergies=" + allergies + "&cuisine=" + cuisine + "&category=" + category);
    const result = await response.json();
    console.log(result);
}

submitButton.addEventListener("click", handleMealPlannerRequest); 

function handleAddAllergy(e, ui){
    e.preventDefault();
    userAllergies.push(ui.item.value)
    localStorage.setItem("userAllergies", JSON.stringify(userAllergies));
    displayAllergyList();
}

function handleRemoveAllergy(allergen){
    var index = userAllergies.indexOf(allergen);
    userAllergies.splice(index, 1);
    localStorage.setItem("userAllergies", JSON.stringify(userAllergies));
    displayAllergyList();
}

function displayAllergyList(){
    const allergens = document.getElementById("result-allergens");
    allergens.textContent = ""; 
    
    userAllergies.forEach(function(allergen) {
        var listItem = document.createElement("li");
        listItem.textContent = allergen;
        listItem.setAttribute("id", "allergy-" + allergen);
        listItem.style.listStyle = 'none';
        allergens.appendChild(listItem);
        var removeButton = document.createElement("button");
        removeButton.textContent = "Remove";
        removeButton.classList.add("remove-btn");
        listItem.appendChild(removeButton);
        removeButton.addEventListener("click", function(e){
            handleRemoveAllergy(allergen);
        });
    });
}

displayAllergyList();


async function handleMealPlannerRequest() {
    let allergies = userAllergies.join(',');
    let cuisine = cuisineInput.value;
    let category = categoryInput.value;

    const response = await fetch(`/api/meal-planner?allergies=${allergies}&cuisine=${cuisine}&category=${category}`);
    const result = await response.json();

    const resultsContainer = document.getElementById("search-results");
    resultsContainer.innerHTML = ""; // clear previous results

    const topMeals = result.slice(0, 3);
    for (const meal of topMeals) {
        const mealDetailsResp = await fetch(`https://www.themealdb.com/api/json/v1/1/lookup.php?i=${meal.idMeal}`);
        const mealDetails = await mealDetailsResp.json();
        const mealData = mealDetails.meals[0];

        const mealCard = document.createElement("div");
        mealCard.classList.add("meal-card");

        // Meal Image
        const mealImg = document.createElement("img");
        mealImg.src = mealData.strMealThumb;
        mealImg.alt = mealData.strMeal;
        mealCard.appendChild(mealImg);

        // Meal Name
        const mealName = document.createElement("h3");
        mealName.textContent = mealData.strMeal;
        mealCard.appendChild(mealName);

        // Ingredients List
        const ingredientsList = document.createElement("ul");
        for (let i = 1; i <= 20; i++) {
            const ingredient = mealData[`strIngredient${i}`];
            const measure = mealData[`strMeasure${i}`];
            if (ingredient && ingredient.trim() !== "") {
                const li = document.createElement("li");
                li.textContent = `${ingredient} - ${measure}`;
                ingredientsList.appendChild(li);
            }
        }
        mealCard.appendChild(ingredientsList);

        // Instructions
        const instructions = document.createElement("p");
        instructions.textContent = mealData.strInstructions;
        mealCard.appendChild(instructions);

        resultsContainer.appendChild(mealCard);
    }
}


const mealImg = document.createElement("img");
mealImg.src = mealData.strMealThumb;
mealImg.alt = mealData.strMeal;
mealImg.style.width = "100%";
mealImg.style.borderRadius = "15px";
mealCard.prepend(mealImg); // adds image at the top

