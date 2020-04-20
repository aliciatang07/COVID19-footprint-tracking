import boto3
import json


with open("config/conf.json", "r") as f:
    param_dict = json.load(f)
aws_access_key = param_dict['aws_access_key_id']
aws_secret_access_key = param_dict['aws_secret_access_key']
session = boto3.session.Session(
    aws_access_key_id = aws_access_key,
    aws_secret_access_key = aws_secret_access_key)


region = "us-east-1"
dynamodb = session.resource('dynamodb', region_name=region)
dynamodb_client = session.client('dynamodb',region_name=region)

#get all items: table.scan()

def create_usertable():

    existing_tables = dynamodb_client.list_tables()['TableNames']
    if 'user' not in existing_tables:
        table = dynamodb.create_table(
        TableName = "user",
        AttributeDefinitions=[
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            }
        ],
        KeySchema=[
            {
                'AttributeName': 'user_id',
                'KeyType': 'HASH'
            }],
        ProvisionedThroughput = {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
        )

       # Wait until the table exists.
        table.meta.client.get_waiter('table_exists').wait(TableName="user")

        # Print out some data about the table.
        print("Table status:", table.table_status)
    else:
        print("user table exists")


def create_footprinttable():
    existing_tables = dynamodb_client.list_tables()['TableNames']
    if 'footprint' not in existing_tables:

        table = dynamodb.create_table(
        TableName = "footprint",
        AttributeDefinitions=[
            {
                'AttributeName': 'uuid',
                'AttributeType': 'S'
            },{
                'AttributeName': 'date',
                'AttributeType': 'S'
            }
        ],
        KeySchema=[
            {
                'AttributeName': 'date',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'uuid',
                'KeyType': 'RANGE'
            }],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'userindex',
                    'KeySchema': [
                        {
                            'AttributeName': 'uuid',
                            'KeyType': 'HASH'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
            ],
        ProvisionedThroughput = {
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        })

        table.meta.client.get_waiter('table_exists').wait(TableName="footprint")

    # Print out some data about the table.
        print("Table status:", table.table_status)
    else:
        print("footprint table exists")


def update_data(table_name,keypair,updatelist):
    table = dynamodb.Table(table_name)
    # support action: put|delete
    # actionlist = {"wulala": {"Value": "99999", "Action": 'PUT'}, "lon": {"Value": "333", "Action": 'PUT'}}
    response = table.update_item(
        Key=keypair,
        AttributeUpdates= updatelist
    )
    print(response)


def insert_data(table_name,data):
    # make sure the data is json format
    table = dynamodb.Table(table_name)
    response = table.put_item(
        Item=data
    )
    # print(response)

def remove_data(table_name,keypair):
    table = dynamodb.Table(table_name)
    #eg keypair = {
        #     'username': 'janedoe',
        #     'last_name': 'Doe'
        # }
    table.delete_item(
        Key= keypair
    )

def batch_put_items(table_name,datalist):
    requestcontent = []
    for data in datalist:
        requestcontent.append({'PutRequest':{'Item':data}})
    dynamodb.batch_write_item(
        RequestItems={
            table_name: requestcontent
        })

def get_item(table_name,keypair):
    table = dynamodb.Table(table_name)
    #eg: keypair= {"user_id": "1004"}
    item = table.get_item(Key=keypair)
    if("Item" in item.keys()):
        item = item["Item"]
    else:
        item = None
    print("get item {}".format(item))
    return item


def remove_table(table_name):
    table = dynamodb.Table(table_name)
    table.delete()


def batch_remove(table_name,user_id,key_list):

    table = dynamodb.Table(table_name)
    try:
        with table.batch_writer() as batch:
            for i in key_list:
                batch.delete_item(
                    Key={
                        'date': i["date"],
                        'uuid': user_id+"_"+i["row"]
                    }
                )
                print(user_id+"_"+i["row"])

    except:
        print("get error")

# if __name__ == '__main__':
#     # create_usertable()
#     remove_table("footprint")
#     create_footprinttable()

    # table = dynamodb.Table('user')
    # response = table.scan()
    # print(response)

    # remove_table("user")
    # create_usertable()
    # keypair = {"uuid":"123_9"}



    # data1 = {"uuid":"123_9","date": "123", "time":"12-23", "duration":50}
    # data2 = {"uuid":"123_12","date": "124", "time":"12-23", "duration": 40, "lat": "20", "lon": "-30"}
    # data3 = {"uuid":"233_23","date": "125", "time":"12-23", "duration": 30}
    # # data1 = {"user_id": "1004", "password": "biubibuu", "survey_result": "suspicious", "survey_path": "sddfs.txt"}
    # # data2 = {"user_id": "1005", "password": "biubibuu", "survey_result": "no", "survey_path": "sddfsdfsfs.txt"}
    # # data3 = {"user_id": "1006", "password": "biddeeeubibuu", "survey_result": "suspicious", "survey_path": "sfdsoifnddfs.txt"}
    # datalist = []
    # datalist.append(data1)
    # datalist.append(data2)
    # datalist.append(data3)
    # batch_put_items('footprint',datalist)

    # table = dynamodb.Table("footprint")
