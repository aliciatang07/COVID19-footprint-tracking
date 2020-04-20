# COVID-19 FOOTPRINT TRACKING AND ANALYSIS 

## main functionality
1. record potential and confirmed patient's past 14 days footprint 
2. render the footprint in google map： javascript access s3 file, 
python flask provide proper path (choose date)
3. conduct relevant analysis based on footprint 
4. generate csv file by date and autorefresh every hour by background process 
5. medical survey to check if user are potential patients

## extension
can be used for any other infectious diseases in the future, just change 
the survey content and database 


## TODO LIST 
- [x] interface for recording user's footprint 
- [x] save user footprint data in csv and s3
- [x] dynamodb creation for user 
- [x] google map rendering with footprint 
- [ ] data analytics for footprint 
- [x] survey for checking potential cases 
- [ ] function testing 
- [ ] background process to update s3  
- [x] deployment by lambda and zappa 
- [ ] cost model 
- [ ] large scale testing and provide api for testing like A1
- [ ] UI improvement 

## MUST HAVE TECH
- [x] S3: footprint.csv, survey.txt(allow upload different survey)
- [x] Dynamo:
- [x] lambda

## Database design 
DynamoDB 
1) table for user: \
user_id, hashed password, salt, survey_result, path to survey result detail saved in S3
2) table for footprint record: \
uuid(user_id+row_num):uuid = user_id+"_"+str(i), date, time, duration, lat(string and float whentake out ), lon(string and float whentake out ), (serious degree)

## data retrieving pipeline!
1. save each footprint to date.json in local path(~/footprint/) as form of {lat:float , lon:float }
2. write a finalize_date_data.py to update all files to s3 only past 7 files,RUN BY cron job everyday
3. frontend javascript side retrieve date.json from S3 

## requirement 

1. All persisted data should be stored on DynamoDB and S3. Use them appropriately.
2. You should use Lambda to deploy your application.
3. In addition to the main web functionality, your application should also include a separate
process that runs in the background and does something useful for your application (for
example, doing some analytics on collected data, garbage collection or something else).
4. You can use Zappa or similar tools to deploy your application, but you must not use
Zappa to deploy the background process, rather you should work directly with Lambda
functions.
5. You should create a model for the total AWS costs incurred by deploying your
application on AWS. Take all the AWS services you use (Lambda, API Gateway, S3,
Network bandwidth, …) into account and predict the long-term deployment cost of your
application based on these parameters:
a. Average number of users in a month that will be using your application


In your model, assume typical and reasonable user behaviour.
For this project you can use as many AWS services as you want. AWS has many services (such
as image recognition, speech detection, geographical services, etc) that your application could
benefit from. Feel free to use them. The purpose here is to show modern applications can be
built quickly by connecting already available services.