import json
import base64
import boto3
import math, random
import uuid
import time

rek_client=boto3.client("rekognition")
dynamodb_client = boto3.client('dynamodb') 

def lambda_handler(event, context):
    id = event["FaceId"]
    dynamodb_client.delete_item(TableName='visitors',
        Key={'UID':{'S' : id}} )
    
    response = rek_client.list_faces(
        CollectionId='assignment2',
        MaxResults=123
    )
    
    faceId = ""
    for i in response["Faces"]:
        if i["ExternalImageId"] == id:
            print(i)
            faceId = i["FaceId"]
            
    response = rek_client.delete_faces(
        CollectionId='assignment2',
        FaceIds=[
            faceId,
        ]
    )
    
    print(response)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Succefully ')
    }