# AWSStaticWebSiteStack
Cloud Formation Stack for Static Web Site on AWS

This Stack is used to create all resources needed to create a Static Web Site in AWS. After the execution it will create the folowing resources:
* S3 Bucket for Static Content;
* S3 Bucket for Logs;
* Cloudfront Distribution;
* AWS Public Certificate;
* Route53 alias record for WebSite;
* CodeCommit Repository;
* CodeBuild project to Build the Static Web Site based on NPM;
* CodePipeline configured to run the build after repository commit on master branch.

For proper working you must provide the folowing resources:
* Hosted Zone configured in AWS Route53.

## Intermediate Resources
During stack creation a few intermediate resources are needed, mainly to automate the certificate approval process. At this moment, four lambda functions will be created at your account to perform the certification validation. After stack creation they are not needed and can be safely deleted. But if you delete them, you can find problems when you try to delete the stack using CloudFormation.

## Usage
For stack creation, you'll need a environment with awscli and python3. Clone the repo in this environment and run the script generate.py with the following parameters:
|Option|Details|Explanation|
|-------|------|------|
|-s/--stack|(Required)|Cloud Formation stack name;|
|-z/--HostedZoneId|(Required, if run is true)|Route53 Hosted Zone Id to be used as domain name;|
|-n/--HostName|(Required, if run is true)|Host Name for WebSite;|
|-b/--BuildPipeline|(Optional)|Create CodeCommit Repository, CodeBuild Project and CodePipeline for Continuous Deployment;|
|-p/--profile|(Optional)|awscli profile name;|
|-r/--run|True if present|Run the Create Stack Command (If false, it only upload the stack and functions to S3 and you can start the creation from console).|
|-------|------|------|

## Post Usage
After the stack creation you can use any Single Page Application Framework based on npm to deploy your site. These are the steps to integrate you development workflow to the StaticWebSite Pipeline:
1. Create a new folder for you project*;
2. In the root folder, copy the buildspec_template.yml file and rename it to buildspec.yml;
3. From the Stack Outputs, copy S3SiteBucket;
3. Edit the buildspec.yml and change the name of the folder for the project build and the name of the S3Bucket using the stack output;
4. Initialize a git repo int the project root folder;
5. From the Stack Outputs, copy the RepositoryCloneUrl;
6. Add the remote repository to your local git repository;
7. Create a feature/development branch in your repository and put your source code;
8. When tested and ready for deployment, merge the feature/development branch in master and push to the remote repo;
9. Wait for the project build (you can monitor the build from CodeBuild Console our aws-cli);
10. From the Stack Outputs, copy the WebsiteURL and open it in a browser;

\* If you use the same folder of the the stack, keep in mind that you'll need to have two different remote repos in the same local repo.

## AWS Costs
The creation of these AWS resources does not incurr costs. However you will incur the costs as soon as you start serving content from your just created site. For information about the costs, check [the official AWS link for Cloud Front Distribution Pricing](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/CloudFrontPricing.html)

## AWS Security and Roles
For the stack creation, you must use a IAM User with permissions to:
* Create/Delete IAM Service Roles;
* Create/Update/Delete S3 Buckets and Bucket Configurations (ACL, StaticWebSite, Logging);
* Create/Update/Delete S3 Objects;
* Create/Update/Delete Lambda Functions;
* Create/Update/Delete CodeCommit Repositories/Codepipeline Pipelines/CodeBuild projects;
* Create/Update/Delete Cloudwatch Events/Event Rules;
* Request/Delete Certificates (ACM);
* Create/Update/Delete Cloudfront Distributions.

For this, you can start the stack creation with a user with AdministratorAccess Policy or append the stackCreationPolicy in this repository to your user.

## Warning
If you delete the stack in CloudFormation all the resources in the bukects will be cleared by the stack process deletion.

## Configuration
### CloudFront cache
When in development phase, it is better to test your application using the S3 static web site url, instead of WebSiteUrl that is configured to use CloudFront. That option is best because the CloudFront was configured to cache the requested files for 86400 seconds (1 day). Using the S3 Static Web Site address you can get the updated files as soon as the CodeBuild project ends.

You must consider this cache interval in the case of current deployment of your website. If you need imediate deployment over the CloudFront edge locations you must invalidate the cached objects after deployment or change the cache interval used in distribution. Considering that the cache invalidation will incurr costs, this procedure was not implemented in the stack. You must perform it manually.

If you want to change the cache interval for any reason, you just need to change the parameter CACHE_CONTROL in buildspec.yml file. Just keep in mind that this value will be used for all the next builds and only will be available after the previous cache interval where expired or the caches were invalidated (again, cache invalidation costs money)!

## Nexts Steps
1. Implement RetainPolicy for buckets (not working, because of [this](https://stackoverflow.com/questions/34286395/))
2. Implement CORS options for Static Web Site;
3. Generate buildspec.yml with bucket name generated by stack;
4. Implement stack creation on generate script;
5. Implement stack monitoring on generate script;
6. Automatic create Angular project and add remote CodeCommit repository to project.

## Bugs and Improvements
If you find a bug in the stack templates or in lambda functions, please open an issue in this github repo. It would be better if you create a new branch, fix the bug or implement the improvement and submit a pull request. ;-)