# AWSStaticWebSiteStack
Cloud Formation Stack for Static Web Site on AWS

This Stack is used to create all resources needed to create a Static Web Site in AWS. After the execution it will create the folowing resources:
* S3 Bucket for Static Content;
* S3 Bucket for Logs;
* Cloudfront Distribution;
* Route53 alias for site;
* AWS Public Certificate.

For proper working you must provide the folowing resources:
* Hosted Zone configured in AWS Route53;
* S3 Bucket for Stack resources;

## Intermediate Resources
During stack creation a few intermediate resources are needed, mainly to automate the certificate approval process. At this moment, three lambda funcionts will be created at your account to perform the certification validation.

## Usage
For stack creation, you'll need a environment with awscli and python3. Clone the repo in this environment and run the script generate.py with the following parameters:
* -p/--profile      (Optional) awscli profile name;
* -s/--stack        (Required) cloud formation stack name;
* -b/--bucket       (Required) existent s3 bucket for stack resources and files;
* -z/--HostedZoneId  (Required) Route53 Hosted Zone Id to be used as domain name.

## AWS Costs
The resources created does not incurr costs. You'll have the costs associated with S3 storage for your WebSite objects and CloudFront data transfer costs when your site were active.

## Nexts Steps
1. Refactor lambda function to concentrate the three in one.
2. Create a CodeCommit repository for static site code;
3. Create a CodePipeline Job to build and deploy the code.
