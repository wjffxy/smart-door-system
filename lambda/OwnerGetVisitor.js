const AWS = require('aws-sdk');
AWS.config.update({region: 'us-east-1'});
const ddb = new AWS.DynamoDB({apiVersion: '2012-08-10'});

exports.handler = async (event) => {
    console.log(event.FaceId);
    var params = {
      ExpressionAttributeValues: {
        ':s': {S: event.FaceId}
      },
      KeyConditionExpression: 'UID = :s',
      TableName: 'visitors'
    };
    var rep =  await ddb.query(params).promise();
    console.log(rep.Items.length);
    if(rep.Count == 0){
      return {
        statusCode: 404,
        body: JSON.stringify('No Such Item'),
      };
    } else {
      return rep.Items[0];
    }
};
