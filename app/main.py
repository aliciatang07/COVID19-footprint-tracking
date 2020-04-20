LOCAL_ENV = 0
DATABASE_USE_RDS=0
GALLERY_LOCAL_DEBUG=0
from flask import render_template, url_for, session,jsonify
from app import webapp
from botocore.exceptions import ClientError

import json
import boto3
from datetime import date
import datetime

S3_BUCKET_NAME = "assessmentresult"
IAM_ROLE_NAME = ""
COVID_API_ROOT = "https://api.covid19api.com/dayone/"
import io



def check_logged_in():
    logged = False
    # Session has "user" field and "logged" field
    if "user" in session and "logged" in session:
        logged = True
    return logged

def get_login_status_webpage():
    logged = False
    username = ""
    if "user" in session and "logged" in session:
        logged = True
        username = session["user"]
    return logged, username

@webapp.route('/')
def main():
    logged, username = get_login_status_webpage()
    return render_template("main.html" ,logged=logged, username=username, title="COVID-19 Tracking")



@webapp.route('/fetch_analysis/new')
def fetch_analysis_new():
    # S3.download_file_to_object()
    s3 = get_resource()
    today = date.today()
    filename = today.strftime("%Y-%m-%d")+".json"
    if(check_file_exists(filename,s3,"covidfootprint")):
        json_test = json.load(download_file_to_object(filename,s3,"covidfootprint"))
    else:
        json_test = default_data_helper()
    return jsonify(json_test)

@webapp.route('/fetch_analysis/cumulative')
def fetch_analysis_cumulative():
    # S3.download_file_to_object()
    s3 = get_resource()
    today = date.today()
    filename = today.strftime("%Y-%m-%d")+"cumulative.json"
    if(check_file_exists(filename,s3,"covidfootprint")):
        json_test = json.load(download_file_to_object(filename,s3,"covidfootprint"))
    else:
        json_test = default_data_helper()
    return jsonify(json_test)


def default_data_helper():
    data = []
    for i in range(14):
        today = date.today()
        day = today - datetime.timedelta(days=i)
        day = day.strftime("%Y-%m-%d")
        data.append({day: 0})
    return data

def get_resource():
    with open("config/conf.json", "r") as f:
        param_dict = json.load(f)
    aws_access_key = param_dict['aws_access_key_id']
    aws_secret_access_key = param_dict['aws_secret_access_key']
    session = boto3.session.Session(
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_access_key)
    s3 = session.resource("s3")
    return s3


def download_file_to_object(name_on_s3,s3,bucketname):
    raw_stream = s3.Object(bucketname, name_on_s3.lower()).get()["Body"]
    out_bytes = raw_stream.read()
    out_stream = io.BytesIO(out_bytes)
    out_stream.seek(0)
    return out_stream

def check_file_exists(name_on_s3,s3,bucketname):
    retry_times = 2
    while retry_times > 0:
        try:
            s3.Object(bucketname, name_on_s3.lower()).load()
        except ClientError as e:
            if ("Token" in e.response["Error"]["Code"] or
                "400" in e.response["Error"]["Code"] or
                "403" in e.response["Error"]["Code"]):
                retry_times -= 1
                if retry_times == 0:
                    return False
                else:
                    print("Token expired, renewing")
                    get_resource()
                    continue
            else:
                return False
        else:
            return True
        break
