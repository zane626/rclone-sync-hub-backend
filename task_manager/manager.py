from utils.db import get_db

def initialize_the_project():
    collection = get_db()['folders']
    collection.find({'status': ''})
