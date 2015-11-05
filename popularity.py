#!/usr/bin/env python

# Copyright 2015 datawire. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pymysql
import re
import sys
import threading
import uuid
import yaml

from flask import Flask, jsonify
app = Flask(__name__)

# Note:
# index and service_id do not have any bearing on your service; they're just useful for tracking deployed services
# when debugging.
index = 0
service_id = uuid.uuid4()

config = {}
environ = "development"

query = "SELECT username, karma FROM users WHERE banned_at IS NULL ORDER BY karma DESC"

def synchronized(func):
    func.__lock__ = threading.Lock()

    def synchronized_func(*args, **kwargs):
        with func.__lock__:
            return func(*args, **kwargs)

    return synchronized_func

@synchronized
def increment_index():
    global index
    index += 1

def inefficient_query():
    import time
    # this is just for demo purposes... let's do something really stupid like sleep in our method
    time.sleep(10)

    increment_index()
    db = connect(config[environ]['database'])
    cur = db.cursor()
    cur.execute(query)
    users = cur.fetchall()
    db.close()
    return users

def efficient_query():
    increment_index()
    db = connect(config[environ]['database'])
    cur = db.cursor()
    cur.execute(query)
    users = cur.fetchall()
    db.close()
    return users

@app.route("/")
def query_most_popular_users():

    """ returns information about the most popular users in the lobsters database by comparing their accrued karma
    balance

    :return:
    """

    #users = inefficient_query()
    users = efficient_query()

    return jsonify(service_id=str(service_id), index=index, users=users)

@app.route("/health")
def health_check():
    increment_index()
    return jsonify(service_id=str(service_id), index=index, status='OK')


def env_regex(loader, node):
    value = loader.construct_scalar(node)
    var = pattern.match(value).groups()[0]
    return os.environ[var]

def connect(db_config):
    return pymysql.connect(
        charset=db_config['charset'],
        cursorclass=pymysql.cursors.DictCursor,
        db=db_config['database'],
        host=db_config['host'],
        password=db_config['password'],
        port=int(db_config['port']),
        user=db_config['username']
    )

if __name__ == "__main__":
    pattern = re.compile(r'^<%= ENV\[\'(.*)\'\] %>$')
    yaml.add_implicit_resolver('!env_regex', pattern)

    def env_regex(loader, node):
        value = loader.construct_scalar(node)
        var = pattern.match(value).groups()[0]
        return os.environ[var]

    yaml.add_constructor('!env_regex', env_regex)

    passed_args = sys.argv
    with open(passed_args[2], 'r') as f:
        config = yaml.load(f)

    # only using debug=True for the nice auto-reload on change feature
    environ = passed_args[1]
    app.run(debug=True, port=int(config[environ]['web']['port']), host=str(config[environ]['web']['listen']))
