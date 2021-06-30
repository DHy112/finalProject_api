import json

with open('config.json', 'r') as f:
    config = json.load(f)

AWS_ACCESS_KEY = config['AWS']['AWS_ACCESS_KEY']
AWS_SECRET_KEY = config['AWS']['AWS_SECRET_KEY']
BUCKET_NAME = config['AWS']['BUCKET_NAME']

DB_HOST = config['MariaDB']['host']
DB_USER = config['MariaDB']['user']
DB_PW = config['MariaDB']['password']
DB_DATABASE = config['MariaDB']['database']


