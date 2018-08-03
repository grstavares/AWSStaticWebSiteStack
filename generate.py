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
masterStack = "stacks/master.json"
stackList = ["stacks/functions.json", "stacks/certificate.json", "stacks/website.json", "stacks/pipeline.json"]
lambdaList = ["lambdas/requestCertificate.js", "lambdas/approveCertificate.js", "lambdas/checkCertificateApproval.js"]
filesToClear = []
#filesList = stackList + lambdaList
bucketNameSubstitutionPattern = "{-INSERT BUCKET NAME WITH STACK TEMPLATES HERE-}"
verbose = False

def parseArgs():

    parser = argparse.ArgumentParser("AWS StaticWeb Site Stack Creation")
    parser.add_argument("-p", "--profile", help="AWS CLI Profile")
    parser.add_argument("-s", "--stack", help="Stack Name", required=True)
    parser.add_argument("-z", "--HostedZoneId", help="HostedZone registred in Route53 (must exist)")
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
        newContent = fileContent.replace(bucketNameSubstitutionPattern, bucketName)

        outputName = masterStack + "-updated"
        with open(outputName, "w") as output:
            print(newContent, file=output)
            return outputName

        return masterStack

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
        s3object.put(Body=open(file, 'rb'))

def clearZipped(files):

    if verbose:
        print("Cleaning zip files on local dir...")

    for file in files:
        #os.remove(file)
        print("Must remove " + file)


args = parseArgs()
awscliProfile = args.profile
verbose = args.verbose

filestoBeChecked = stackList + lambdaList
filestoBeChecked.append(masterStack)

print(filestoBeChecked)
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

print("Script Done!")