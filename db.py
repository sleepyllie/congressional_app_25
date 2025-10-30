import sqlite3
import json
from datetime import datetime

import click
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            "app-db",
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def read_json_from_file(file_path):
    with open(file_path, "r") as file:
        file_content = []
        line = file.readline()
        while line:
            file_content.append(line)
            line = file.readline()

    json_data = []
    for line in file_content:
        json_data.append(json.loads(line))

    return json_data

def load_json_data():
    db = get_db()
    cursor = db.cursor()

    # load food 
    '''
    json_data = read_json_from_file("data/Food.json")
    query = """ 
        insert into food
        (public_id, name, name_scientific, description)
        values (?, ?, ?, ?);
    """
    for row in json_data:
        params = (row["public_id"], row["name"], row["name_scientific"], row["description"])
        cursor.execute(query, params)
        db.commit()
    '''
    '''
    # load compound data 
    json_data = read_json_from_file("data/Compound.json")
    query = """
        insert into compound
        (public_id, name, description)
        values (?, ?, ?);
    """

    for row in json_data:
        params = (row["public_id"], row["name"], row["description"])
        cursor.execute(query, params)
        db.commit()

    # load nutrient data
    json_data = read_json_from_file("data/Nutrient.json")
    query = """
        insert into nutrient
        (public_id, name, description)
        values (?, ?, ?);
    """

    for row in json_data:
        params = (row["public_id"], row["name"], row["description"])
        cursor.execute(query, params)
        db.commit()
    '''

    # load content
    cursor.execute("delete from content")
    db.commit()

    json_data = read_json_from_file("data/Content.json")
    query = """
        insert into content
        (compound_id, nutrient_id, food_id, orig_content, orig_unit)
        values (?, ?, ?, ?, ?);
    """

    for row in json_data:
        if row["source_type"] == "Nutrient":
            params = (None, row["source_id"], row["food_id"], 
                  row["orig_content"], row["orig_unit"]
                )
        else:
            compound_query = """
                select * from compound where public_id like ?; 
            """
            cursor.execute(compound_query, ("%" + str(row["source_id"]), ))
            compounds = cursor.fetchall()
            if len(compounds) > 0:
                compound = compounds[0]
                compound_id = compound["id"]
            else:
                compound_id = row["source_id"]
                
            params = (compound_id, None, row["food_id"], 
                  row["orig_content"], row["orig_unit"]
            )
            
        cursor.execute(query, params)
        db.commit()

@click.command('load-json-data')
def load_json_data_command():
    load_json_data()
    click.echo('Loaded JSON data.')

sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(load_json_data_command)