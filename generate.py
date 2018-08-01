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
stackList = ["stacks/master.json", "stacks/functions.json", "stacks/certificate.json", "stacks/website.json", "stacks/pipeline.json"]
lambdaList = ["lambdas/requestCertificate.js", "lambdas/approveCertificate.js", "lambdas/checkCertificateApproval.js"]
filesList = stackList + lambdaList
verbose = False

def parseArgs():

    parser = argparse.ArgumentParser("AWS StaticWeb Site Stack Creation")
    parser.add_argument("-p", "--profile", help="AWS CLI Profile")
    parser.add_argument("-s", "--stack", help="Stack Name", required=True)
    parser.add_argument("-b", "--bucket", help="S3 Bucket for Stack Resources (must exist)")
    parser.add_argument("-z", "--HostedZoneId", help="HostedZone registred in Route53 (must exist)")
    parser.add_argument("-v", "--verbose", help="Show steps", action="store_true")

    return parser.parse_args()

def checkInputFiles():
    
    if verbose:
        print("Checking files on local dir...")

    listChecked = []
    for file in filesList:
        listChecked.append(os.path.isfile(file))

    return all(listChecked)

def zipFiles(files):

    if verbose:
        print("Compressing Lambda Code...")

    zipfiles = []
    for file in files:
        zipname = os.path.splitext(file)[0] + ".zip"
        with zipfile.ZipFile(zipname, 'w') as zipped:
            zipped.write(file, arcname=os.path.basename(file))
            zipfiles.append(zipname)

    return zipfiles

def getS3():
    if awscliProfile == None:
        return boto3.resource('s3')
    else:
        session = boto3.Session(profile_name=awscliProfile)
        return session.resource('s3')

def upload(files, bucket):

    if verbose:
        print("Uploading files to S3...")

    s3 = getS3()
    for file in files:
        s3object = s3.Object(bucket, file)
        s3object.put(Body=open(file, 'rb'))

def clearZipped(files):

    if verbose:
        print("Cleaning zip files on local dir...")

    for file in files:
        os.remove(file)


args = parseArgs()
awscliProfile = args.profile
verbose = args.verbose

if not checkInputFiles():
    raise ValueError('Stack Files not available on current dir!')

bucketName = args.bucket
zipped = zipFiles(lambdaList)
upload(stackList + zipped, bucketName)
clearZipped(zipped)

print("Script Done!")
# s3 = getS3()
# for bucket in s3.buckets.all():
#    print(bucket.name)