from flask import render_template, url_for, session, request, redirect, jsonify
from app import webapp
from app import dynamo
from app.dynamo import dynamodb

from app.main import check_logged_in, get_login_status_webpage
from app.validation import isdate, istime, isfloat, isEmpty

import base64
import urllib


@webapp.route("/footprint_delete",methods = ['GET','POST'])
def footprint_delete():
    if request.method == "POST":
        remove_list = request.json["data"]
        print(remove_list)
        if (check_logged_in()):
            user_id = session["user"]
            print("start deleting user{}".format(user_id))
            dynamo.batch_remove("footprint", user_id, remove_list)
        else:
            print("Error: NOT LOGGED IN ")

    return redirect(url_for("footprint_upload"))


@webapp.route("/footprint_upload", methods = ['GET'])
def footprint_upload():
    logged, username = get_login_status_webpage()
    validation_error = False

    if "validation_error" in session:
        validation_error = True
        session.pop("validation_error", None)

    if (check_logged_in()):
        user_id = session["user"]
        if "footprintcipher" in session:
            with_storage = True
        else:
            with_storage = False
        return render_template("footprint_collect.html", 
            user_id=user_id, 
            username=username, 
            logged=logged, 
            title="Footprint Submission", 
            with_storage=with_storage,
            validation_error=validation_error
        )
    else:
        return redirect(url_for("main"))

@webapp.route("/footprint_upload_submit", methods=["POST"])
def footprint_upload_submit():
    if (check_logged_in()):
        user_id = session["user"]

        print(request.form)
        length = request.form.get("rowCount")
        rowarray = request.form.get("rowList").split(",")
        print(rowarray)
        row_list = []
        key_list = []
        data = []
        # if length != None:
        for i in rowarray:
            ######ADD INVALID INPUT CHECK !!!! AND ERROR HANDLING ###
            uuid = user_id+"_"+str(i)
            date = request.form.get("date"+str(i))
            print(date)
            time = request.form.get("time"+str(i))
            print(time)
            duration = request.form.get("duration"+str(i))
            lat = request.form.get("lat" + str(i))
            lon = request.form.get("lon" + str(i))

            # Validation
            if (not isdate(date) or not istime(time) or 
                not isfloat(duration) or not isfloat(lat) or
                not isfloat(lon)):
                session["validation_error"] = True
                return redirect(url_for("footprint_upload"))

            # need further consideration

            cur_list = []
            rowdata = {
                       "time":{"Value": time, "Action": 'PUT'},"duration":{"Value": duration, "Action": 'PUT'},
                       "lat":{"Value": lat, "Action": 'PUT'},"lng":{"Value": lon, "Action": 'PUT'}}
            key = {"date":date,"uuid":uuid}
            # rowdata = {"uuid": uuid, "date": date, "time": time, "duration": duration, "lat": lat, "lng": lon}
            row_list.append(rowdata)
            key_list.append(key)
            # cur_list.append(uuid)
            cur_list.append(date)
            cur_list.append(time)
            cur_list.append(duration)
            cur_list.append(lat)
            cur_list.append(lon)
            data.append(cur_list)

        # for j in range(len(date_json_list)):
        #     S3.upload_file(file_path+date_json_list[j],date_json_list[j])

        print(data)
        filename = date +".json"
        keypair = {"user_id":user_id}
        updatelist = {"footprint_path": {"Value": filename, "Action": 'PUT'}}
        dynamo.update_data("user",keypair,updatelist)
        batch_helper("footprint",row_list,key_list)
        # dynamo.batch_put_items("footprint", row_list)
        #make sure user_id is UNIQUE otherwise overwirte


        return redirect(url_for("footprint_upload"))
    else:
        return redirect(url_for("main"))



@webapp.route("/footprint_select_location")
def footprint_select_location():
    row = request.args.get("row")
    lat = request.args.get("lat", "NaN")
    lon = request.args.get("lon", "NaN")
    return render_template("footpoint_select.html", row=row, lat=lat, lon=lon)

@webapp.route('/footprint_load')
def footprint_load():
    if (check_logged_in()):
        user_id = session["user"]
        print(user_id)
        olddata = get_user_footprint(user_id)

        return jsonify(olddata)




# Input: Base64, urlencoded
@webapp.route("/footprint_storage", methods=["POST"])
def footprint_storage():
    if check_logged_in():
        cipher = request.form.get("cipher")
        rows = request.form.get("rows")
        if "footprintcipher" in session:
            session.pop("footprintcipher", None)
        session["footprintcipher"] = cipher
        session["footprintrows"] = rows

        return "OK"
    else:
        return "Unauthorized!", 403

# Output: JSON object
@webapp.route("/footprint_readstorage", methods=["GET"])
def footprint_readstorage():
    if not check_logged_in():
        return "Unauthorized!", 403
    if "footprintcipher" not in session or "footprintrows" not in session:
        return "No stored footprints", 403

    cipher = session.get("footprintcipher")
    rows_raw = session.get("footprintrows")
    table_data = base64.b64decode(cipher.encode("ascii")).decode("ascii")
    print(table_data)
    table_data = urllib.parse.parse_qs(table_data)

    # Delete stored footprint (remove if draft storage becomes a feature)
    session.pop("footprintcipher", None)
    session.pop("footprintrows", None)

    keys = ["row", "date", "time", "duration", "lat", "lon"]
    keys_2 = ["uuid", "date", "time", "duration", "lat", "lng"]
    rows = base64.b64decode(rows_raw.encode("ascii")).decode("ascii")
    rows = str.split(rows, ",")
    rows = sorted(rows)

    standard_data = []
    for (i, row) in enumerate(rows):
        standard_data.append({})
        for (j, key) in enumerate(keys):
            data = table_data.get(key + row, [""])[0]
            if key == "row":
                standard_data[i][keys_2[j]] = "anything_" + data
            else:
                standard_data[i][keys_2[j]] = data

    return jsonify(standard_data)


@webapp.route("/footprint_location_change", methods=["POST"])
def footprint_location_change():
    if not check_logged_in():
        return "Unauthorized!", 403

    lat = request.form.get("lat")
    lng = request.form.get("lng")
    rowId = request.form.get("row", "")

    if "footprintcipher" not in session:
        return "No stored footprints", 403

    cipher = session.get("footprintcipher")
    table_data = base64.b64decode(cipher.encode("ascii")).decode("ascii")
    print(table_data)
    table_data = urllib.parse.parse_qs(table_data, keep_blank_values=True)

    for key in table_data:
        table_data[key] = table_data[key][0] 

    if "lat" + rowId in table_data:
        table_data["lat" + rowId] = lat
        table_data["lon" + rowId] = lng
    print(table_data)

    table_data = urllib.parse.urlencode(table_data)
    cipher = base64.b64encode(table_data.encode("ascii")).decode("ascii")
    session["footprintcipher"] = cipher

    return "OK"




def get_user_footprint(user):

    table = dynamodb.Table('footprint')
    response = table.scan(
        IndexName='userindex',
        ScanFilter={
            'uuid': {
                'AttributeValueList': [user+"_"],
                'ComparisonOperator':  'BEGINS_WITH'
            }
        },
    )

    json_list = []
    for i in response['Items']:
        print(i)
        json_list.append(i)
    return json_list

def batch_helper(table_name,row_list,key_list):
    for i in range(len(row_list)):
        keypair = key_list[i]
        update_list = row_list[i]
        dynamo.update_data(table_name, keypair, update_list)
