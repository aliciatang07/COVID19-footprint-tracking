from datetime import date
import datetime


import boto3
import io
import json

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


S3_BUCKET_NAME = "covidfootprint"


def define_resource():
    global s3, bucket, s3_client, dynamodb

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
    
    region = "us-east-1"
    dynamodb = session.resource('dynamodb', region_name=region)

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


def get_json_data(date):
    table = dynamodb.Table('footprint')
    response = table.query(
        KeyConditionExpression=Key('date').eq(date)
    )
    if(response['Items'] == None):
        return 0
    return len(response['Items'])

if __name__ == '__main__':
    # New cases
    define_resource()
    number = 14
    today = date.today()
    data = []
    filename = today.strftime("%Y-%m-%d")+".json"
    start_date = today - datetime.timedelta(days=number)

    for i in range(int(number)):
        day = start_date + datetime.timedelta(days=i)
        day = day.strftime("%Y-%m-%d")
        data.append({day:get_json_data(day)})

    print(data)

    # upload analysis to S3 for further analysis
    if(check_file_exists(filename)):
            delete_file(filename)
    upload_file_from_object(json.dumps(data),filename)

    # Cumulative cases
    number = 180
    today = date.today()
    data = []
    cumulative_data = 0
    filename = today.strftime("%Y-%m-%d")+"cumulative.json"
    start_date = today - datetime.timedelta(days=number)

    for i in range(int(number)):
        day = start_date + datetime.timedelta(days=i)
        if day >= date(2020, 1, 1):
            day = day.strftime("%Y-%m-%d")
            day_data = get_json_data(day)
            cumulative_data += day_data
            data.append({ day: cumulative_data })

    print(data)

    if(check_file_exists(filename)):
            delete_file(filename)
    upload_file_from_object(json.dumps(data),filename)

    # delete yesterday file
    three_month_ago = today - datetime.timedelta(days=90)
    three_month_ago = three_month_ago.strftime("%Y-%m-%d")+".json"
    print(three_month_ago)
    if (check_file_exists(three_month_ago)):
       delete_file(three_month_ago)



# crontab update every half day
#   * */12 * * * python background_process.py