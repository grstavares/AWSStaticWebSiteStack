var aws = require("aws-sdk");
var resourceName = "emptyBucketToken";

exports.handler = function(event, context) {

    if (event.RequestType == "Update" || event.RequestType == "Create") {
        sendResponse(event, context, "SUCCESS", resourceName, {"Message" : "ClearBuckets not need to run when Stack is Created or Updated!"});
        return;
    }

    console.log("clearBuckets for =>" + JSON.stringify(event));
    var siteBucket = event.ResourceProperties.siteBucket;
    var logsBucket = event.ResourceProperties.logsBucket;

    if (clearBuckets(event, context, [logsBucket, siteBucket])) {
        
        sendResponse(event, context, "SUCCESS", resourceName, {"Message" : "Buckets Cleared!"});
        
    }

};

function clearBuckets(event, context, buckets) {
    
    var s3 = new aws.S3();
    
    for (var idx in buckets) {
        
        var bucket = buckets[idx];
        var listParam = {"Bucket": bucket};
        console.log(listParam);
        
        s3.listObjects(listParam, function (err, data) {
    
            if (err) {
                sendResponse(event, context, "FAILED", resourceName, {"Message" : err});
                return false;
            }
    
            var items = data.Contents;
            var keys = items.map(item => {return {"Key": item.Key}});
            var param = {
                "Bucket": bucket,
                "Delete": {"Objects": keys, "Quiet": true}
            };
    
            console.log("Removing " + keys.length + " objects in Bucket " + bucket);
            
            s3.deleteObjects(param, function(err, data) {
                
            if (err) {
                sendResponse(event, context, "FAILED", resourceName, {"Message" : err});
                return false;
            }
                
            return true;
                
            });
    
        });
        
    }
    
}

function sendResponse(event, context, responseStatus, resourceId, responseData) {
    
    const responseMessage = responseStatus == "SUCCESS" ? "See the details in CloudWatch Log Stream: " + context.logStreamName : JSON.stringify(responseData.Message);

    var responseBody = JSON.stringify({
        Status: responseStatus,
        Reason: responseMessage,
        PhysicalResourceId: resourceId,
        StackId: event.StackId,
        RequestId: event.RequestId,
        LogicalResourceId: event.LogicalResourceId,
        Data: responseData
    });

    console.log("Sending response " + responseStatus + ": " + responseBody);

    var https = require("https");
    var url = require("url");
 
    var parsedUrl = url.parse(event.ResponseURL);
    var options = {
        hostname: parsedUrl.hostname,
        port: 443,
        path: parsedUrl.path,
        method: "PUT",
        headers: {
            "content-type": "",
            "content-length": responseBody.length
        }
    };
 
    var request = https.request(options, function(response) {
        context.done();
    });
 
    request.on("error", function(error) {
        console.log("sendResponse Error:" + error);
        context.done();
    });
  
    request.write(responseBody);
    request.end();

}