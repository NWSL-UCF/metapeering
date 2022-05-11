import boto3
import json

def lambda_handler(event, context):
    s3 = boto3.client("s3")

    if event:
        # Retrieve object from s3 (lambda trigger)
        print("Event: ", event)
        bucket = event['Records'][0]['s3']['bucket']['name']
        filename = str(event['Records'][0]['s3']['object']['key'])
        print("Filename: ", filename)

        try:
            s3_file = s3.get_object(Bucket = bucket, Key = filename)
            file_content = s3_file["Body"].read().decode('utf-8')
            print(file_content)
            return json.loads(file_content)

        except Exception as e:
            print(e)
            print('An error occurred while trying to get object {} from bucket {}.' .format(filename, bucket))
            raise e

    return
