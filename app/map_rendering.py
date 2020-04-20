from flask import render_template, url_for, session, request,redirect, jsonify,Response
from app import webapp
import mimetypes
import requests
import boto3
from app import S3
from app.dynamo import dynamodb
from app.main import get_login_status_webpage
from boto3.dynamodb.conditions import Key
import json


def get_json_data(date):
    table = dynamodb.Table('footprint')
    response = table.query(
        KeyConditionExpression=Key('date').eq(date)
    )
    json_list = []
    for i in response['Items']:
        print(i)
        json_list.append(i)
    return json_list

# search by day
@webapp.route('/map',methods= ['GET','POST'])
def render_footprint():
    logged, username = get_login_status_webpage()

    if request.method == 'POST':
        date = request.form.get("date")
        type = request.form.get("maptype")
        print(date)
        print(type)
        if(type == "heatmap"):
            return redirect(url_for("render_heatmap", date=date))
                # redirect("/render_heatmap/{}".format(date))
        else:
            return redirect(url_for("render_groupmarker",date=date))
                # redirect("/render_groupmarker/{}".format(date))
    else:
        return render_template("footprint-render.html", logged=logged, username=username, title="COVID-19 Tracking Map")


@webapp.route('/render_heatmap/<string:date>')
def render_heatmap(date):
    logged, username = get_login_status_webpage()
    return render_template("footprint_render_heatmap.html", logged=logged, username=username, title="Heatmap", date=date)

@webapp.route('/render_groupmarker/<string:date>')
def render_groupmarker(date):
    logged, username = get_login_status_webpage()
    return render_template("footprint_render_groupmarker.html", logged=logged, username=username, title="Group Marker" ,date=date)


@webapp.route('/render_groupmarker/api/<string:date>')
def groupmarker_api(date):
    # test_json = json.load(S3.download_file_to_object(date+".json"))
    # print(test_json)
    test_json = get_json_data(date)
    print(test_json)
    return jsonify(test_json)


@webapp.route('/render_heatmap/api/<string:date>')
def heatmap_api(date):
    # pick the json date data
    # test_json = json.load(S3.download_file_to_object(date + ".json"))
    # print(test_json)
    test_json = get_json_data(date)
    print(test_json)
    return jsonify(test_json)
