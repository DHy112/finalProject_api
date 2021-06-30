import boto3, pymysql
import config_parser as config


def db_connection():
    conn = pymysql.connect(host=config.DB_HOST,
                           port=3306,
                           user=config.DB_USER,
                           password=config.DB_PW,
                           database=config.DB_DATABASE
                           )
    return conn


def s3_connection():
    s3 = boto3.client(
        's3',
        aws_access_key_id=config.AWS_ACCESS_KEY,
        aws_secret_access_key=config.AWS_SECRET_KEY
    )
    return s3
