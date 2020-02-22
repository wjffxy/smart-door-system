const AWS = require('aws-sdk');
AWS.config.update({region: 'us-east-1'});
const ddb = new AWS.DynamoDB();

exports.handler = async (event) => {
    var otp = event.otp;
    var Id = event.id;
    console.log(event.id);
    console.log(event.otp);
    
    var info = null;
    
    var dynamoDbParams = {
        TableName: 'passcodes',
        KeyConditionExpression: "#pc = :pppp",
        ExpressionAttributeNames:{
            "#pc": "UID"
        },
        ExpressionAttributeValues: {
            ":pppp": {S : Id}
        }
    };
    console.log(dynamoDbParams);
    return  await  ddb.query(dynamoDbParams).promise()
    .then( async (data) => {
        console.log(data.Items[0].Passcode.S);
        if (data.Items[0].Passcode.S  == otp) {
            var params = {
                TableName: 'visitors',
                KeyConditionExpression: "#id = :id",
                ExpressionAttributeNames:{
                    "#id": "UID"
                },
                ExpressionAttributeValues: {
                    ":id": {S :  Id }
                }
            }
            info =await ddb.query(params).promise();
            return {
                statusCode : 200,
                message : "Welcome, " + info.Items[0].Name.S + "! Please come in!"
            };
        } else {
            console.log("otp invalid");
            return { 
                statusCode : 400,
                message : "invalid otp"
            };
        }
    });
};
