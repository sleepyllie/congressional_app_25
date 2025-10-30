var shoppingList = JSON.parse(localStorage.getItem("shoppingList") || "[]");
var shoppingListData = [];
console.log(shoppingList);

async function loadShoppingListData() {
    for (const id of shoppingList) {
        var response = await fetch("/api/usda/food/" + id);
        const result = await response.json();
        shoppingListData.push(result);
    }
    displayShoppingList();
}

function displayShoppingList() {
    const listContainer = document.getElementById("list-content");
    listContainer.textContent = "";

    shoppingListData.forEach(function(item) {
        // Main container for shopping item
        var listItem = document.createElement("div");
        listItem.classList.add("shopping-list-item");

        // Title row (name + remove button)
        var titleRow = document.createElement("div");
        titleRow.style.display = "flex";
        titleRow.style.justifyContent = "space-between";
        titleRow.style.alignItems = "center";

        var nameSpan = document.createElement("span");
        nameSpan.textContent = item.name;
        nameSpan.style.fontWeight = "600";

        var removeButton = document.createElement("button");
        removeButton.textContent = "Remove";
        removeButton.classList.add("remove-button");

        titleRow.appendChild(nameSpan);
        titleRow.appendChild(removeButton);
        listItem.appendChild(titleRow);

        // Ingredients section (hidden by default)
        var ingredientsDiv = document.createElement("div");
        ingredientsDiv.style.display = "none";
        ingredientsDiv.style.marginTop = "10px";

        if (item.ingredients && item.ingredients.length > 0) {
            var ingList = document.createElement("ul");
            ingList.style.paddingLeft = "20px";
            item.ingredients.forEach(ing => {
                var li = document.createElement("li");
                li.textContent = ing;
                ingList.appendChild(li);
            });
            ingredientsDiv.appendChild(ingList);
        } else {
            ingredientsDiv.textContent = "No ingredients available.";
        }

        listItem.appendChild(ingredientsDiv);

        // Toggle button for ingredients
        var toggleBtn = document.createElement("button");
        toggleBtn.textContent = "Show Ingredients ▼";
        toggleBtn.style.marginTop = "8px";
        toggleBtn.style.cursor = "pointer";
        toggleBtn.style.background = "#0097a7";
        toggleBtn.style.color = "white";
        toggleBtn.style.border = "none";
        toggleBtn.style.borderRadius = "8px";
        toggleBtn.style.padding = "6px 12px";

        toggleBtn.addEventListener("click", function() {
            if (ingredientsDiv.style.display === "none") {
                ingredientsDiv.style.display = "block";
                toggleBtn.textContent = "Hide Ingredients ▲";
            } else {
                ingredientsDiv.style.display = "none";
                toggleBtn.textContent = "Show Ingredients ▼";
            }
        });

        listItem.appendChild(toggleBtn);

        // Remove button functionality
        removeButton.addEventListener("click", function() {
            listItem.remove();
            var index = shoppingList.indexOf(item.id);
            if (index > -1) shoppingList.splice(index, 1);
            localStorage.setItem("shoppingList", JSON.stringify(shoppingList));
        });

        listContainer.appendChild(listItem);
    });
}

loadShoppingListData();
