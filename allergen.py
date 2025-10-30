import json, requests

ALLERGY_TABLE = {
    "gluten": ["WHEAT", "BARLEY", "RYE", "FARRO", "BREWER'S YEAST", "SPELT", "KAMUT", "TRITICALE", "MALT"],
    "dairy": ["MILK", "WHEY", "CASEIN", "LACTOSE", "BUTTER", "GHEE", "CHEESE", "YOGURT", "CREAM", "LACTALBUMIN"],
    "soy": ["SOY", "SOYBEAN", "SOY PROTEIN", "EDAMAME", "TOFU", "TEMPEH", "MISO", "NATTO"],
    "nuts": ["PEANUT", "CASHEW", "WALNUT", "ALMOND", "PECAN", "HAZELNUT", "MACADAMIA", "PISTACHIO", "PINE NUT", "GROUNDNUT", "ARACHIS", "MARZIPAN", "PESTO"],
    "fish" : ["SALMON", "TUNA", "ANCHOVY", "HERRING", "ANCHOVY", "SURIMI", "FISH", "BOTTARGA", "ROE", "KATSUOBUSHI"],
    "shellfish": ["OYSTER", "CLAM", "SCALLOP", "SHRIMP", "CRAB", "LOBSTER", "PRAWN", "MUSSEL"],
    "sesame": ["SESAME", "TAHINI"],
    "eggs": ["EGG", "EGG WHITE", "EGG YOLK", "ALBUMIN", "OVOMUCOID", "OVALBUMIN", "LYZOSZYME"],
    "mustard" : ["MUSTARD"],
    "celery": ["CELERY", "CELERIAC", "CELERY SEED"],
    "lupin" : ["LUPIN"],
    "sulfites" : ["SULFUR DIOXIDE", "SODIUM SULFITE", "SODIUM BISULFITE", "SODIUM METABISULFITE", "POTASSIUM BISULFITE"],
    "corn" : ["CORN", "ZEA MAYS"],
    "citric acid" : ["CITRIC ACID"],
    "spices" : ["PAPRIKA", "CURRY"]

}

def get_allergens_from_ingredients(ingredients):
    results = []
    for allergy in ALLERGY_TABLE.keys():
        found = False
        for ingredient in ingredients:
            if ingredient.upper() in ALLERGY_TABLE[allergy]:
                found = True
            else:
                for allergen in ALLERGY_TABLE[allergy]:
                    if ingredient.upper().find(allergen) >= 0:
                        found = True
        if found:
            results.append(allergy)
                
    return results

def get_list_of_allergies():
    return list(ALLERGY_TABLE.keys())

# check meal for allergies
def is_meal_safe_for_allergies(meal, allergies):
    is_safe = True
    allergens = get_allergens_from_ingredients(meal["ingredients"])
    for allergy in allergies:
        if allergy in allergens:
            is_safe = False

    return is_safe


def filter_meals_by_allergy_safety(meals, allergies):
    results = []
    for meal in meals:
       meal_data = fetch_meal_data(meal["idMeal"])
       if is_meal_safe_for_allergies(meal_data, allergies):
           results.append(meal_data)

    return results

def fetch_meal_data(id):
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={id}"
    response = requests.get(url)
    json_data = json.loads(response.text)["meals"][0]
    json_data["ingredients"] = []
    for i in range(1, 21):
        ingredient = json_data[f"strIngredient{i}"]
        if ingredient is not None and len(ingredient) > 0:
            json_data["ingredients"].append(ingredient.upper())

    return json_data