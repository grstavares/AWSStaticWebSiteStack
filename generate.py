#!/usr/local/bin/python

__description__ = 'Python Script to Copy Stack Files to S3 and start the Stack Creation'
__author__ = 'Gustavo Tavares'
__version__ = '1.0'
__date__ = '2018/07/31'

"""
Source code put in public domain by Gustavo Tavares, no Copyright
Use at your own risk

History:
  2018/07/31: start

Todo:
"""

import boto3
import argparse
import os
import zipfile
import time

awscliProfile = None
verbose = False

masterStack = "stacks/master.json"
stackList = ["stacks/functions.json", "stacks/s3buckets.json", "stacks/certificate.json", "stacks/distribution.json", "stacks/pipeline.json"]
lambdaList = ["lambdas/requestCertificate.js", "lambdas/approveCertificate.js", "lambdas/checkCertificateApproval.js", "lambdas/getHostedZoneName.js", "lambdas/clearBuckets.js"]
filesToClear = []

stackBucketsPattern = "{-INSERT BUCKET NAME WITH STACK TEMPLATES HERE-}"
siteBucketPattern = "{-INSERT BUCKET NAME FOR STATIC WEBSITE HERE-}"
siteStackPattern = "{-INSERT ANGULAR PROJECT NAME HERE-}"

def parseArgs():

    parser = argparse.ArgumentParser("AWS StaticWeb Site Stack Creation")
    parser.add_argument("-p", "--profile", help="AWS CLI Profile")
    parser.add_argument("-s", "--stack", help="Stack Name", required=True)
    parser.add_argument("-z", "--HostedZoneId", help="AWS route53 HostedZoneId")
    parser.add_argument("-n", "--HostName", help="HostName for WebSite")
    parser.add_argument("-r", "--run", help="Run the command in awscli to create the Stack", action="store_true")
    parser.add_argument("-v", "--verbose", help="Show steps", action="store_true")

    return parser.parse_args()

def checkInputFiles(filesList):
    
    if verbose:
        print("Checking files on local dir...")

    listChecked = []
    for file in filesList:
        listChecked.append(os.path.isfile(file))

    return all(listChecked)

def generateBucketName(stackName):
    stack = stackName.lower()
    name = "-stackdefinitions-"
    timestamp = str(int(time.time()))
    return stack + name + timestamp

def getSession():
    if awscliProfile == None:
        return boto3.Session()
    else:
        return boto3.Session(profile_name=awscliProfile)

def createBucket(bucketName):
    
    if verbose:
        print("Creating S3 Bucket " + bucketName + "...")

    region = getSession().region_name
    s3 = getSession().resource('s3')
    s3.create_bucket(Bucket=bucketName, CreateBucketConfiguration={'LocationConstraint': region})
    return

def updateBucketInStack(fileName, bucketName):
    
    file = open(fileName, "r")
    if file.mode == 'r':

        fileContent = file.read()
        newContent = fileContent.replace(stackBucketsPattern, bucketName)

        outputName = masterStack + "-updated"
        with open(outputName, "w") as output:
            print(newContent, file=output)
            return outputName

        return masterStack

def updateBucketInBuildSpec(fileName, bucketName, stackName):
    
    file = open(fileName, "r")
    if file.mode == 'r':

        fileContent = file.read()
        newContent = fileContent.replace(siteBucketPattern, bucketName)
        newContent = newContent.replace(siteStackPattern, stackName)

        outputName = "buildspec.yml"
        with open(outputName, "w") as output:
            print(newContent, file=output)
            return outputName

        return fileName

def zipFiles(files):

    if verbose:
        print("Compressing Lambda Code...")

    zipfiles = []
    for file in files:
        zipname = os.path.splitext(file)[0] + ".zip"
        with zipfile.ZipFile(zipname, 'w') as zipped:
            zipped.write(file, arcname=os.path.basename(file))
            zipfiles.append(zipname)
            filesToClear.append(zipname)

    return zipfiles

def upload(files, bucket):

    if verbose:
        print("Uploading files to S3...")

    s3 = getSession().resource('s3')
    for file in files:
        s3object = s3.Object(bucket, file.replace("-updated",""))
        s3object.put(Body=open(file, 'rb'), ACL='bucket-owner-full-control')

def clearZipped(files):

    if verbose:
        print("Cleaning zip files on local dir...")

    for file in files:
        os.remove(file)


def startStackCreation(stackName, stackBucket, hostedZoneId, hostName):

    if not hostedZoneId:
        raise ValueError('Stack can not be created with a empty HostedZoneId!')

    if not hostName:
        raise ValueError('Stack can not be created with a empty HosteName!')

    if verbose:
        print("Starting Stack creation...")

    session = getSession()
    region = session.region_name
    templateUrl = "https://" + stackBucket + ".s3.amazonaws.com/stacks/master.json"
    print(bucketUrl)

    cloudformation = session.client('cloudformation')
    response = cloudformation.create_stack(
        StackName = stackName,
        TemplateURL = templateUrl,
        Parameters=[
            {'ParameterKey': 'HostedZone', 'ParameterValue': hostedZoneId, 'UsePreviousValue': True},
            {'ParameterKey': 'HostName', 'ParameterValue': hostName, 'UsePreviousValue': True},
            {'ParameterKey': 'AlternativeDomains', 'ParameterValue': 'none', 'UsePreviousValue': True},
            {'ParameterKey': 'BucketName', 'ParameterValue': stackBucket, 'UsePreviousValue': True}
        ],
        TimeoutInMinutes=60,
        Capabilities=['CAPABILITY_NAMED_IAM'],
    )

args = parseArgs()
awscliProfile = args.profile
createStack = args.run
verbose = args.verbose

filestoBeChecked = stackList + lambdaList
filestoBeChecked.append(masterStack)

if not checkInputFiles(filestoBeChecked):
    raise ValueError('Stack Files not available on current dir!')

stackName = args.stack
bucketName = generateBucketName(stackName)

newMasterStack = updateBucketInStack(masterStack, bucketName)
if newMasterStack != masterStack:
    stackList.append(newMasterStack)
    filesToClear.append(newMasterStack)
else:
    stackList.append(masterStack)

createBucket(bucketName)
zipped = zipFiles(lambdaList)
upload(stackList + zipped, bucketName)
clearZipped(filesToClear)

if createStack:
    startStackCreation(stackName, bucketName, args.HostedZoneId, args.HostName)

message = "Stack Creation for " + stackName + " started!" if createStack else "Files uploaded to S3 Bucket-> " + bucketName
print(message)