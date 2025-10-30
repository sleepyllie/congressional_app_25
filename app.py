from flask import Flask, render_template, request, jsonify #type: ignore
import json, requests, concurrent.futures #type: ignore
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

app = Flask(__name__)

import db
db.init_app(app)

from allergen import get_allergens_from_ingredients, get_list_of_allergies, filter_meals_by_allergy_safety

USDA_API_KEY = "Mli7HlGkltI3Sjpf0n56qJrMMLnaE0fKurEQTOrG" 

# @app.route('/old-home')
# def index():
#     return render_template("home.html")

@app.route('/')
def index():
    return render_template("home.html")

@app.route('/search')
def off_search():
    return render_template("search.html")

@app.route('/shopping-list')
def shopping_list():
    return render_template("shopping_list.html")

@app.route('/meal-planner')
def meal_planner():
    return render_template("meal_planner.html")

@app.route('/about_us')
def about_us():
    return render_template("about_us.html")

@app.route('/food')
def food():
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("select * from food")
    food_rows = cursor.fetchall()
    output = ""
    for row in food_rows:
        print(row)
        output += f"<p> ID: {row['id']} Public ID: {row['public_id']} Name: {row['name']} Scientific Name: {row['name_scientific']} Description: {row['description']} </p>"

    return output

@app.route('/food/<name>')
def search_for_food(name = None):
    db_conn = db.get_db() # db connection object
    cursor = db_conn.cursor() # loading cursor: specifices query params
    cursor.execute("select * from food where name like ?;", ("%" + name + "%",)) # define which query to run
    rows = cursor.fetchall() # runs the select query
    row = rows[0]
    output = f"<p> <b>ID:</b> {row['id']} </p> <p><b>Public ID:</b> {row['public_id']}</p> <p><b>Name:</b> {row['name']}</p> <p><b>Scientific Name:</b> {row['name_scientific']}</p> <p><b>Description:</b> {row['description']} </p>"

    content_query = """
        select nutrient.name as name, content.orig_content as amount, content.orig_unit as unit from content 
        join nutrient on content.nutrient_id = nutrient.id
        where food_id = ?;

    """
    cursor.execute(content_query, (row["id"],))
    content_rows = cursor.fetchall()
    
    # TODO add content data to output.
    output += "<ul>"
    for row in content_rows:
        output += f"<li>{row['amount']}{row['unit']} of {row['name']}</li>"
    output += "</ul>"
    return output

@app.route('/api/food/search/<name>')
def api_search_for_food(name = None):
    db_conn = db.get_db() # db connection object
    cursor = db_conn.cursor() # loading cursor: specifices query params
    cursor.execute("select * from food where name like ?;", ("%" + name + "%",)) # define which query to run
    rows = cursor.fetchall() # runs the select query
    row = rows[0]

    results = {"id": row["id"], "name": row["name"], "name_scientific": row["name_scientific"], "description": row["description"]}

    content_query = """
        select content.id as id, nutrient.name as name, avg(content.orig_content) as amount, content.orig_unit as unit from content 
        join nutrient on content.nutrient_id = nutrient.id
        where food_id = ? and 
        nutrient.name not like '%%undifferentiated%' and
        nutrient.name not like '%%:%'
        group by nutrient.name
        order by nutrient.name;
    """

    cursor.execute(content_query, (row["id"],))
    content_rows = cursor.fetchall()

    results["nutrients"] = []
    for content in content_rows:
        results["nutrients"].append({
            "name": content["name"],
            "amount": round(content["amount"], 2),
            "unit": content["unit"],
            "id": content["id"]
        })

    compound_content_query = """
        select content.id as id, compound.name as name, avg(content.orig_content) as amount, content.orig_unit as unit from content 
        join compound on content.compound_id = compound.id
        where food_id = ? and 
        compound.name not like '%%undifferentiated%' and
        compound.name not like '%%:%' and
        substr(compound.name, 1, 1) not in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '(', 'Δ', 'α', 'β', 'γ', 'δ', 'ε', 'ω') and
        content.orig_unit is not null and content.orig_content is not null and
        content.orig_content > 0
        group by compound.name
        order by compound.name;
    """

    cursor.execute(compound_content_query, (row["id"],))
    compound_rows = cursor.fetchall()

    results["compounds"] = []
    for compound in compound_rows:
        results["compounds"].append({
            "name": compound["name"],
            "amount": round(compound["amount"], 2),
            "unit": compound["unit"],
            "id": compound["id"]
        })
    return json.dumps(results)

@app.route('/api/food/search-for-foods/')
def api_search_for_foods():
    name = request.args.get("term")
    db_conn = db.get_db() 
    cursor = db_conn.cursor() 
    cursor.execute("select name from food where name like ? limit 10;", ("%" + name + "%",))
    rows = cursor.fetchall() 
    names = []
    for row in rows: 
        names.append(row["name"])

    return json.dumps(names)

@app.route('/api/usda/food/<fdc_id>')
def get_usda_food(fdc_id = None):
    url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={USDA_API_KEY}"
    #url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={name}&action=process&search_simple=1&json=1&sort_by=unique_scans_n&page_size=10"
    print(url)
    response = requests.get(url)
    json_data = json.loads(response.text)
    ingredients = json_data["ingredients"].split(', ')
    allergens = get_allergens_from_ingredients(ingredients)
    results = {
        "raw_data": json_data, 
        "allergens": allergens, 
        "name": json_data["description"], 
        "ingredients" : ingredients,
        "id": json_data["fdcId"]
    }
    return json.dumps(results)


@app.route('/api/usda/food/search/')
def api_search_usda_for_foods():
    name = request.args.get("term")
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={name}&dataType=Branded,Foundation,Survey%20%28FNDDS%29,SR%20Legacy&pageSize=10&pageNumber=1&sortBy=dataType.keyword&sortOrder=asc&api_key={USDA_API_KEY}"
    response = requests.get(url)
    json_data = response.json()
    results = []

    # List of overarching companies to ignore
    ignored_companies = ["Ferrero", "Nestle", "PepsiCo", "Kraft", "General Mills", "Unilever"]

    for food in json_data.get("foods", []):
        brand = food.get("brandOwner", "") or food.get("brandName", "")
        description = food.get("description", "")

        # Only prepend brand if it's not empty, not in ignored list, and not already in description
        if brand and brand not in ignored_companies and brand.lower() not in description.lower():
            display_name = f"{brand} {description}".strip()
        else:
            display_name = description.strip()

        results.append({
            "label": display_name,   # for autocomplete display
            "value": food.get("fdcId"), 
            "brand": brand,
            "description": description
        })

    return json.dumps(results)


@app.route('/api/meal-planner/')
def api_meal_planner():
    raw_allergies = request.args.get("allergies")
    cuisine = request.args.get("cuisine")
    category = request.args.get("category")

    allergies = raw_allergies.split(',')
    response = requests.get(f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category}")
    category_meals = json.loads(response.text)["meals"]

    response = requests.get(f"https://www.themealdb.com/api/json/v1/1/filter.php?a={cuisine}")
    cuisine_meals = json.loads(response.text)["meals"]
    
    if len(cuisine_meals) > 0:
        for meal in category_meals[:]:
            if meal not in cuisine_meals:
                category_meals.remove(meal)

    filtered_meals = filter_meals_by_allergy_safety(category_meals, allergies)
    
    return json.dumps(filtered_meals)

@app.route('/api/meal-planner/categories')
def get_categories():
    search = request.args.get("term")
    categories = ["Beef", "Breakfast", "Chicken", "Dessert", "Goat", "Lamb", "Miscellaneous", 
                  "Pasta", "Pork", "Seafood", "Side", "Starter", "Vegan", "Vegetarian"]

    results = []
    for category in categories:
        if category.find(search) >= 0:
            results.append(category)
    return json.dumps(results)

@app.route('/api/meal-planner/cuisines')
def get_cuisines():
    search = request.args.get("term")
    cuisines = ["American", "British", "Canadian", "Chinese", "Croatian", "Dutch", "Egyptian", "Filipino", "French",
                "Greek", "Indian", "Irish", "Italian", "Jamaican", "Japanese", "Kenyan", "Malaysian", "Mexican", "Moroccan", 
                "Polish", "Portuguese", "Russian", "Spanish", "Syrian", "Thai", "Tunisian", "Turkish", "Ukrainian", "Uruguayan", 
                "Vietnamese"]

    results = []
    for cuisine in cuisines:
        if cuisine.find(search) >= 0:
            results.append(cuisine)
    return json.dumps(results)

@app.route('/api/allergies')
def get_allergies():
    search = request.args.get("term")
    allergies = get_list_of_allergies()
    results = []
    for allergen in allergies:
        if allergen.find(search) >= 0:
            results.append(allergen)
    return json.dumps(results)


def extract_keywords(description):
    """Return set of meaningful keywords from a description."""
    ignore_words = {"all", "types", "raw", "fresh", "cooked", "frozen", "pieces", "shaped"}
    return set(word.lower() for word in description.replace(",", "").split() if word.lower() not in ignore_words)

def similarity_score(orig_keywords, alt_keywords):
    """Return number of shared keywords."""
    return len(orig_keywords & alt_keywords)

@app.route('/api/usda/food/alternatives/<fdc_id>')
def get_usda_alternatives(fdc_id):
    user_allergies = request.args.get("allergies", "")
    allergies = user_allergies.split(',') if user_allergies else []

    # Get original food
    food_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={USDA_API_KEY}"
    food_data = requests.get(food_url).json()
    description = food_data.get("description", "")
    orig_keywords = extract_keywords(description)
    orig_category = food_data.get("foodCategory", "").lower()

    # Use all meaningful keywords for search
    query = " ".join(orig_keywords)
    search_url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={query}&pageSize=20&api_key={USDA_API_KEY}"
    search_results = requests.get(search_url).json()
    foods = search_results.get("foods", [])

    alternatives = []

    def fetch_food_details(food):
        alt_fdc_id = food.get("fdcId")
        if alt_fdc_id == int(fdc_id):
            return None

        try:
            alt_data = requests.get(
                f"https://api.nal.usda.gov/fdc/v1/food/{alt_fdc_id}?api_key={USDA_API_KEY}",
                timeout=10
            ).json()

            # Skip if food category doesn’t match
            alt_category = alt_data.get("foodCategory", "").lower()
            if orig_category and alt_category and alt_category != orig_category:
                return None

            alt_description = alt_data.get("description", "")
            alt_keywords = extract_keywords(alt_description)
            score = similarity_score(orig_keywords, alt_keywords)
            if score == 0:
                return None

            ingredients = alt_data.get("ingredients", "")
            ingredients_list = [i.strip() for i in ingredients.split(",")] if ingredients else []
            food_allergens = get_allergens_from_ingredients(ingredients_list)
            
            if any(a in food_allergens for a in allergies):
                return None

            return {
                "id": alt_fdc_id,
                "name": alt_description,
                "brand": alt_data.get("brandOwner") or "No brand",
                "ingredients": ingredients_list,
                "score": score
            }
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_food = {executor.submit(fetch_food_details, f): f for f in foods}
        for future in as_completed(future_to_food):
            result = future.result()
            if result:
                alternatives.append(result)

    # Sort by similarity score descending, take top 5
    alternatives = sorted(alternatives, key=lambda x: x["score"], reverse=True)[:5]

    return jsonify(alternatives)


# ----- || OLD STUFF || ------- #
@app.route('/nutrients/')
def list_nutrients():
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("select * from nutrient")
    nutrient_rows = cursor.fetchall()
    
    return render_template("nutrients.html", nutrient_rows=nutrient_rows)

@app.route('/compounds/')
def list_compounds():
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("select * from compound")
    compound_rows = cursor.fetchall()
    output = ""
    for row in compound_rows:
        print(row)
        output += f"<p> ID: {row['id']} Public ID: {row['public_id']} Name: {row['name']} Description: {row['description']} </p>"

    return output

@app.route('/content/count')
def count_content():
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("select count(*) as count from content")
    content_row = cursor.fetchall()[0]
    return str(content_row["count"])
