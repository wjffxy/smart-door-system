from __future__ import print_function
import json
import base64
import boto3
import math, random 
import cv2
import numpy as np
import uuid
import time

# function to generate OTP 
def generateOTP() : 
  
    # Declare a digits variable   
    # which stores all digits  
    digits = "0123456789"
    OTP = "" 
  
    # length of password can be chaged 
    # by changing value in range 
    for i in range(4) : 
        OTP += digits[math.floor(random.random() * 10)] 
  
    return OTP 
    
s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')
dynamodb_client = boto3.client('dynamodb') 
rek_client=boto3.client('rekognition')
table_name = 'visitors'
pic_url = ''
ses_client = boto3.client(
    'ses',
    region_name='us-east-1',
    aws_access_key_id='AKIA3F6ZPBUMICQBNLDC',
    aws_secret_access_key='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'
)

sns = boto3.client('sns')

def sendMessageToOwner(pic_url,uid) :
    response = ses_client.send_email(
    Destination={
        'ToAddresses': ['jy2622@nyu.edu'],
    },
    Message={
        'Body': {
            'Text': {
                'Charset': 'UTF-8',
                'Data':"Allow user in? http://assignment2wp1.s3-website-us-east-1.amazonaws.com/?faceId=" + uid,
            },
        },
        'Subject': {
            'Charset': 'UTF-8',
            'Data': "Incoming stranger",
        },
    },
    Source='jy2622@nyu.edu',
    )
    # response = sns.publish(
    #     PhoneNumber='+15178892956',
    #     Message=pic_url +"\n" + "https://assignment2b1.s3.amazonaws.com/WebPage/WP1/index.html/" + uid
    # )
    print(response)

def sendMessageToVisitor(mail,otp, userId) :
    response = ses_client.send_email(
    Destination={
        'ToAddresses': [mail],
    },
    Message={
        'Body': {
            'Text': {
                'Charset': 'UTF-8',
                'Data': "You One-Time Login password is: " + otp + " \nPlease go to http://assignment2wp2.s3-website-us-east-1.amazonaws.com?userId=" + userId
            },
        },
        'Subject': {
            'Charset': 'UTF-8',
            'Data': "password",
        },
    },
    Source='jy2622@nyu.edu',
    )
    print("You One-Time Login password is: " + otp + " \nPlease go to http://assignment2wp2.s3-website-us-east-1.amazonaws.com?userId=" + userId)
    # response = sns.publish(
    #     PhoneNumber= phone,
    #     Message="You One-Time Login password is: " + otp + " \nPlease go to http://assignment2wp2.s3-website-us-east-1.amazonaws.com?userId=" + userId
    # )
    print(response)
def lambda_handler(event, context):
    record = event['Records'][0]
    #content = json.loads(base64.b64decode(record['kinesis']['data']).decode('utf-8'))
    payload=base64.b64decode(record["kinesis"]["data"])
    payload_json = json.loads(payload)
    uid = str(uuid.uuid1())
    if(len(payload_json['FaceSearchResponse']) == 0 or len(payload_json['FaceSearchResponse'][0]['MatchedFaces']) == 0):
        time.sleep(10)
        pp = extract_frame(uid)
        pic_url = 'https://assignment2b1.s3.amazonaws.com/' + uid + '.jpg'
        photo =  uid + '.jpg'
        item = {'UID': {'S': uid},
                'Pic_Url': {'S':pic_url}
               }
        if pp == True :
            dynamodb_client.put_item(TableName=table_name, Item=item)
            response=rek_client.index_faces(CollectionId='assignment2',
                                    Image={'S3Object':{'Bucket':'assignment2b1','Name':photo}},
                                    ExternalImageId=uid,
                                    MaxFaces=1,
                                    QualityFilter="AUTO",
                                    DetectionAttributes=['ALL'])
            sendMessageToOwner(pic_url,uid)
        return
    print(payload_json)
    faceId = str(payload_json['FaceSearchResponse'][0]['MatchedFaces'][0]['Face']['ExternalImageId'])
    print(faceId)
    pic_url = 'https://assignment2b1.s3.amazonaws.com/' + faceId + '.jpg'
    
    tmp = dynamodb_client.query(
        ExpressionAttributeValues= {
            ':s': {'S': faceId}
            
        },
        KeyConditionExpression= 'UID = :s',
        ProjectionExpression= 'UID',
        TableName= 'passcodes'
    )
    print("tmp")
    print(type(tmp))
    if len(tmp['Items']) == 0:
        otp = generateOTP()
        item = {'UID': {'S': faceId},
                'Passcode': {'S':otp}
            }
        dynamodb_client.put_item(TableName='passcodes', Item=item)
        time.sleep(10)
        data=dynamodb_client.get_item(TableName='visitors', 
                                      Key={ 'UID':{ 'S': faceId}}
        )
        data1=dynamodb_client.get_item(TableName='passcodes', 
                                      Key={ 'UID':{ 'S': faceId}}
        )
        print(faceId)
        sendMessageToVisitor(data['Item']['Email']['S'],data1['Item']['Passcode']['S'],faceId)
    else:
        time.sleep(10)
        data=dynamodb_client.get_item(TableName='visitors', 
                                      Key={ 'UID':{ 'S': faceId}}
        )
        data1=dynamodb_client.get_item(TableName='passcodes', 
                                      Key={ 'UID':{ 'S': faceId}}
        )
        print(faceId)
        sendMessageToVisitor(data['Item']['Email']['S'],data1['Item']['Passcode']['S'],faceId)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }


def extract_frame(faceId):
    kvs_client = boto3.client('kinesisvideo')
    kvs_data_pt = kvs_client.get_data_endpoint(
        StreamARN='arn:aws:kinesisvideo:us-east-1:768718343448:stream/KVS1/1572908305136', # kinesis stream arn
        APIName='GET_MEDIA'
    )
    
    print(kvs_data_pt)
    
    end_pt = kvs_data_pt['DataEndpoint']
    kvs_video_client = boto3.client('kinesis-video-media', endpoint_url=end_pt, region_name='us-east-1') # provide your region
    kvs_stream = kvs_video_client.get_media(
        StreamARN='arn:aws:kinesisvideo:us-east-1:768718343448:stream/KVS1/1572908305136', # kinesis stream arn
        StartSelector={'StartSelectorType': 'NOW'} # to keep getting latest available chunk on the stream
    )
    print(kvs_stream)
    pic_name = faceId + '.jpg'
    
    with open('/tmp/stream.mkv', 'wb') as f:
        streamBody = kvs_stream['Payload'].read(1024*2048) # reads min(16MB of payload, payload size) - can tweak this
        f.write(streamBody)
        # use openCV to get a frame
        cap = cv2.VideoCapture('/tmp/stream.mkv')
        # use some logic to ensure the frame being read has the person, something like bounding box or median'th frame of the video etc
        ret, frame = cap.read() 
        cv2.imwrite('/tmp/frame.jpg', frame)
        if np.shape(frame) != ():
            s3_client = boto3.client('s3')
            s3_client.upload_file(
                '/tmp/frame.jpg',
                'assignment2b1', # replace with your bucket name
                pic_name
            )
            cap.release()
            print('Image uploaded')
            return True
        else:
            return False
    return False
        