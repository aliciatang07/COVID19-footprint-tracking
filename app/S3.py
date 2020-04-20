import boto3
import io
import json
import os

from boto3.dynamodb.conditions import Key

from app.main import S3_BUCKET_NAME
from botocore.exceptions import ClientError
from app.dynamo import dynamodb


def define_resource():
    global s3, bucket,s3_client

    with open("config/conf.json", "r") as f:
        param_dict = json.load(f)
    aws_access_key = param_dict['aws_access_key_id']
    aws_secret_access_key = param_dict['aws_secret_access_key']
    session = boto3.session.Session(
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_access_key)
    s3 = session.resource("s3")
    s3_client = session.client("s3")
    bucket = s3.Bucket(S3_BUCKET_NAME)
define_resource()

def upload_file(path_to_file, name_on_s3):
    stream = open(path_to_file, mode='rb')
    bucket.put_object(Key=name_on_s3.lower(), Body=stream)
    stream.close()

def upload_file_from_object(file_obj, name_on_s3):
    retry_times = 2
    while retry_times > 0:
        try:
            bucket.put_object(Key=name_on_s3.lower(), Body=file_obj)
        except ClientError as e:
            if ("Token" in e.response["Error"]["Code"] or
                "Signature" in e.response["Error"]["Code"] or
                "Access" in e.response["Error"]["Code"]):
                retry_times -= 1
                if retry_times == 0:
                    raise
                else:
                    print("Token expired, renewing")
                    define_resource()
                    continue
            else:
                raise
        break

def delete_file(name_on_s3):
    bucket.delete_objects(Delete={
        "Objects": [
            {
                "Key": name_on_s3.lower()
            }
        ]
    })

def delete_files_with_prefix(prefix):
    retry_times = 2
    while retry_times > 0:
        try:
            objects = []
            for obj in bucket.objects.filter(Prefix=prefix):
                objects.append({"Key": obj.key})
            bucket.delete_objects(Delete={"Objects": objects})
        except ClientError as e:
            print(e.response["Error"])
            retry_times -= 1
            if retry_times == 0:
                return False
            else:
                print("Token expired, renewing")
                define_resource()
                continue
        else:
            return True
        break

def download_file_to_object(name_on_s3):
    raw_stream = s3.Object(S3_BUCKET_NAME, name_on_s3.lower()).get()["Body"]
    out_bytes = raw_stream.read()
    out_stream = io.BytesIO(out_bytes)
    out_stream.seek(0)
    return out_stream

def check_file_exists(name_on_s3):
    retry_times = 2
    while retry_times > 0:
        try:
            s3.Object(S3_BUCKET_NAME, name_on_s3.lower()).load()
        except ClientError as e:
            if ("Token" in e.response["Error"]["Code"] or
                "400" in e.response["Error"]["Code"] or
                "403" in e.response["Error"]["Code"]):
                retry_times -= 1
                if retry_times == 0:
                    return False
                else:
                    print("Token expired, renewing")
                    define_resource()
                    continue
            else:
                return False
        else:
            return True
        break


def update_datejson_file(name_on_s3,data):
    if(check_file_exists(name_on_s3)):
        #old_data = json.load(S3.download_file_to_object(name_on_s3))
        delete_file(name_on_s3)
    json_list = json.dumps(data)
    upload_file_from_object(json_list, name_on_s3)

def update_json_file(name_on_s3,data):
    if(check_file_exists(name_on_s3)):
        #old_data = json.load(S3.download_file_to_object(name_on_s3))
        delete_file(name_on_s3)
    json_list = json.dumps(data)
    upload_file_from_object(json_list, name_on_s3)

def update_datejson_fromdb(name_on_s3):
    date = name_on_s3.split(".")[0]
    if (check_file_exists(name_on_s3)):
        # old_data = json.load(S3.download_file_to_object(name_on_s3))
        delete_file(name_on_s3)
    table = dynamodb.Table('footprint')
    response = table.query(
        KeyConditionExpression=Key('date').eq(date)
    )
    json_list = []
    for i in response['Items']:
        print(i)
        json_list.append(i)
    json_list = json.dumps(json_list)
    upload_file_from_object(json_list, name_on_s3)

