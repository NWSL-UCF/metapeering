from chalice import Chalice
import boto3
import json
from mysql.connector import connect, Error
import uuid
from datetime import datetime
import os
import chalicelib.rds_config

app = Chalice(app_name='metapeering_api')

BUCKET_NAME = "metapeering-requests-bucket"
REGION = "us-east-1"
EXPIRATION = 60

@app.route('/generate_url_s3', methods=['GET'])
def generate_url_s3():

    parameters = app.current_request.query_params
    email = parameters['email']
    asn = parameters['filename']

    user_id = uuid.uuid4()
    file_name = str(user_id) + "_" + asn
    create_db_entry(email, user_id)

    s3_client = boto3.client("s3", region_name = REGION)

    try:
        response = s3_client.generate_presigned_url('put_object', ExpiresIn = EXPIRATION, Params={"Bucket" : BUCKET_NAME,
                                                                "Key": file_name,
                                                                "ContentType" : "application/json"})

    except ClientError as e:
        app.log.error(e)
        return json.dumps({'status' : 'Bad Request'})

    return json.dumps({'status' : 'OK', 'response' : response, 'id' : str(user_id)})

def create_db_entry(email, user_id):
    try:
        with connect(
            host = chalicelib.rds_config.AWS_RDS_CONNECTION,
            user = chalicelib.rds_config.AWS_RDS_USER,
            password = chalicelib.rds_config.AWS_RDS_PASSWD,
            database= chalicelib.rds_config.AWS_RDS_DB
        ) as connection:
            id = user_id
            job_status = "IN_PROGRESS"
            now = datetime.now()
            date = now.strftime('%Y-%m-%d %H:%M:%S')
            email = email

            with connection.cursor() as cursor:
                cursor.execute("insert into metapeering_jobs (id, job_status, time_date, email) VALUES (%s, %s, %s, %s)", (str(id), job_status, date, email))
                connection.commit()

    except Error as e:
        print(e)
