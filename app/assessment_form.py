from flask import render_template,request,redirect,session,url_for
from app import webapp
from app.main import check_logged_in, get_login_status_webpage
from app.validation import isdate, istime, isfloat, isEmpty
from app import dynamo
from app import S3
import json

@webapp.route('/assessment',methods=['GET'])
def submit_assessment():
    logged, username = get_login_status_webpage()
    validation_error = False
    if "validation_error" in session:
        validation_error = True
        session.pop("validation_error", None)

    return render_template("self-assessment.html",
        logged=logged,
        username=username,
        title="Take a self-assessment",
        validation_error=validation_error
    )



@webapp.route('/view_assessment_history',methods=['GET'])
def view_assessment_history():
    if (check_logged_in()):
        logged, username = get_login_status_webpage()
        filename = username + ".json"
        if (S3.check_file_exists(filename)):
            obj = json.load(S3.download_file_to_object(filename))
            q1 = obj.get("Have you had in-person closed contact with patients who diagnosed with coronavirus?", "unknown")
            q2 = obj.get("Have you visited a place that patients who diagnosed with coronavirus has been to?", "unknown")
            q3 = obj.get("Have you traveled to foreign countries in the last 14 days?", "unknown")
            q4 = obj.get("symptoms", [])
            result = obj.get("result", "unknown")

            if "suspicious" in result or "emergency" in result:
                risk_level = "danger"
            elif "isolation" in result:
                risk_level = "warning"
            else:
                risk_level = "success"

            return render_template("assessment_history.html",
                assessment_exist=True,
                q1=q1,
                q2=q2,
                q3=q3,
                q4=q4,
                result=result,
                risk_level=risk_level,
                username=username,
                logged=logged,
                title="Assessment History"
            )
        else:
            return render_template("assessment_history.html",
                assessment_exist=False,
                username=username,
                logged=logged,
                title="Assessment History"
            )
        
    else:
        return redirect(url_for("main"))



@webapp.route('/submit_form',methods=['POST'])
def evaluate_results():
    logged, username = get_login_status_webpage()
    if (check_logged_in()):
        user = session["user"]
        fever = request.form.get('fever')
        cough = request.form.get('cough')
        breath = request.form.get('breath')
        chest_pain = request.form.get('chest_pain')
        other_symptoms = request.form.get('other_symptoms')

        one = request.form.get('one')
        two = request.form.get('two')
        three = request.form.get('three')
        if one is None or two is None or three is None:
            session["validation_error"] = True
            return redirect(url_for("submit_assessment"))

        #Analyze the user's answer
        if (fever or cough or breath or chest_pain) and (one == "yes"):
            respond_type = 0
        elif (breath or chest_pain) and (one == "no"):
            respond_type = 1
        elif (fever or cough or other_symptoms) or (one == "yes") or (one == "unknown") or (two == "yes") or (three == "yes"):
            respond_type = 2
        else:
            respond_type = 3

        #find assessment result according to respond_type
        comment = ["Your status is suspicious and you should test for COVID-19","Please call 911 or go directly to nearest emergency",
        "Please do a self-isolation for 14 days and keep monitoring on your health status","You are safe for now. Please keep staying at home"]
        response = comment[respond_type]

        #write result file
        file_path = user + ".json"
        symptoms = []
        if(fever != None):
            symptoms.append(fever)

        if(cough != None):
            symptoms.append(cough)

        if(breath != None):
            symptoms.append(breath)

        if(chest_pain != None):
            symptoms.append(chest_pain)

        if(other_symptoms != ""):
            symptoms.append(other_symptoms)

        json_object = {
            "Have you had in-person closed contact with patients who diagnosed with coronavirus?":one,"Have you visited a place that patients who diagnosed with coronavirus has been to?":two,"Have you traveled to foreign countries in the last 14 days?":three,
            "symptoms":symptoms,"result":response}

        #check if the result file already exists
        if S3.check_file_exists(file_path):
            s3_response = S3.delete_file(file_path)
        #upload new result file to S3 bucket
        data = json.dumps(json_object)
        s3_response2 =S3.upload_file_from_object(data,file_path)

        #dynamodb
        keypair = {"user_id": user}
        updatelist = {"survey_result": {"Value": respond_type, "Action": 'PUT'}}
        updatelist_filepath = {"file_path": {"Value": file_path, "Action": 'PUT'}}
        dynamo.update_data("user", keypair, updatelist)
        dynamo.update_data("user", keypair, updatelist_filepath)

        # Risk level
        if "suspicious" in response or "emergency" in response:
            risk_level = "danger"
        elif "isolation" in response:
            risk_level = "warning"
        else:
            risk_level = "success"

        return render_template('assessment_result.html',
            response=response,
            risk_level=risk_level,
            logged=logged,
            username=username,
            title="Self-Assessment Results"
        )
    else:
        return redirect(url_for("main"))