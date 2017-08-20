#!/usr/bin/python3

from flask import Flask, jsonify, make_response, abort, request, g
from functools import wraps
from werkzeug.contrib.cache import SimpleCache

import json
import os.path
import sqlite3

app = Flask(__name__)

DATABASE = 'db.sqlite3'

cache = SimpleCache()

def init_db():
    if not os.path.isfile(DATABASE):
        init_db()

    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        def make_dicts(cursor, row):
            return dict((cursor.description[idx][0], value)
                        for idx, value in enumerate(row))

        db.row_factory = make_dicts
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def insert_dict(cur, table, my_dict):
    columns = ', '.join(my_dict.keys())
    placeholders = ':'+', :'.join(my_dict.keys())
    query = 'INSERT INTO %s (%s) VALUES (%s)' % (table, columns, placeholders)
    cur.execute(query, my_dict)
    return cur.lastrowid

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def cached(timeout=5 * 60, key='view/%s'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = key % request.path
            rv = cache.get(cache_key)
            if rv is not None:
                return rv
            rv = f(*args, **kwargs)
            cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator

item_types = ['farmableitem', 'simpleitem', 'consumableitem', 'equipmentitem',
              'weapon', 'mount', 'furnitureitem', 'journalitem']

items = []
with open('data/items.json', 'r') as f:
    json = json.load(f)['items']

    for item_type in item_types:
        items += json[item_type]

@cached(0)
@app.route('/items', methods=['GET'])
def get_items():
    return jsonify({'items': items})

@cached(0)
@app.route('/items/<string:item_name>', methods=['GET'])
def get_item(item_name):
    item = [item for item in items if item['uniquename'] == item_name]
    if len(item) == 0:
        abort(404)

    return jsonify(item[0])

@app.route('/orders', methods=['GET'])
def get_orders():
    name = request.args.get('name')
    if name:
        orders = query_db('SELECT * FROM orders WHERE ItemTypeId = ?', [name])
    else:
        orders = query_db('SELECT * FROM orders')

    return jsonify({'orders': orders})

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = query_db('SELECT * FROM orders WHERE id = ?',
                     [order_id], one=True)
    if order is None:
        abort(404)

    app.logger.info(order)
    return jsonify({'order': order})

@app.route('/marketorders.ingest', methods=['POST'])
def ingest_orders():
    if not request.json:
        abort(400)

    with app.app_context():
        db = get_db()
        cur = db.cursor()
        for order in request.json['Orders']:
            order['UnitPriceSilver'] = order['UnitPriceSilver'] / 10000
            insert_dict(cur, 'orders', order)

        db.commit()

    return jsonify({'status': 'ok'}), 200

@app.errorhandler(404)
def handle_404(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
