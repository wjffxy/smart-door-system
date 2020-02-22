const AWS = require('aws-sdk');
AWS.config.update({ region: 'us-east-1' });
const ddb = new AWS.DynamoDB({ apiVersion: '2012-08-10' });
const ses = new AWS.SES({ apiVersion: '2010-12-01' });

function generateOTP() {
    var digits = "0123456789";
    var OTP = "";
  
    // # length of password can be chaged 
    // # by changing value in range 
    for(var i = 0; i < 4; i++){
        OTP += digits[Math.floor(Math.random() * 10)];
    }
    return OTP;
}

exports.handler = async (event) => {
    console.log(event);
    var queryParameter = {
        ExpressionAttributeValues: {
            ':s': { S: event["id"] }
        },
        KeyConditionExpression: 'UID = :s',
        TableName: 'visitors'
    };
    console.log(queryParameter);
    var rep = await ddb.query(queryParameter).promise();
    if (rep.Count == 0) {
        return {
            statusCode: 404,
            body: JSON.stringify('No Such Item'),
        };
    } else {
        var updateParams = {
            ExpressionAttributeNames: {
                "#N": "Name",
                "#PN": "Email"
            },
            ExpressionAttributeValues: {
                ":n": {
                    S: event["name"]
                },
                ":pn": {
                    S: event["email"]
                }
            },
            Key: {
                "UID": rep.Items[0].UID
            },
            TableName: "visitors",
            UpdateExpression: "SET #N = :n, #PN = :pn"
        };

        console.log(updateParams);
        var result = await ddb.updateItem(updateParams).promise();
        console.log(result);

        var otp = generateOTP();
        console.log("OTP");
        console.log(otp);

        var params = {
            Item: {
                "UID": {
                    S: event.id
                },
                "Passcode": {
                    S: otp
                }
            },
            TableName: "passcodes"
        };

        var response = await ddb.putItem(params).promise();


        var message = "The One-Time Password is " + otp + ".\nPlease go to " + "\nhttp://assignment2wp2.s3-website-us-east-1.amazonaws.com?userId=" + event.id;
        var params = {
            Destination: { /* required */
                CcAddresses: [],
                ToAddresses: [
                    event.email
                ]
            },
            Message: { /* required */
                Body: { /* required */
                    Html: {
                        Charset: "UTF-8",
                        Data: message
                    },
                    Text: {
                        Charset: "UTF-8",
                        Data: message
                    }
                },
                Subject: {
                    Charset: 'UTF-8',
                    Data: 'One Time Password'
                }
            },
            Source: 'jy2622@nyu.edu', /* required */
            ReplyToAddresses: [],
        };
        console.log(params);
        var response = await ses.sendEmail(params).promise();
        console.log(response);
    }
};
