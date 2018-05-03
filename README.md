# CodePipeline App Versioning Demo

These instructions demonstrate how to combine AWS CodePipeline, CodeDeploy, & CodeCommit to dynamically generate a version release webpage for an application using CodeDeploy environment variables.

Here is some asci art showing the relationship between files in this repo and services in AWS.
```
--CodePipeline "demo-app"
    |--iam role "codepipeline-service-role"
    |   |--./aws-policies/codepipeline-service-role.json
    |--Repo: CodeCommit "demo-app"
    |--Build: Jenkins "My Jenkins"
    |--Deploy: CodeDeploy
        |--iam user "demo-app-SRE"
        |   |--./aws-policies/codedeploy-user.json
        |--S3 "demo-app"
        |--App name "demo-app"
            |--Deploy group "demo-app-group"
                |--blue/green
                |--ASG "demo-app-asg"
                    |--group "demo-app-asg"
                    |   |--ELB "demo-app"
                    |       |--SG
                    |       |    |--name = "demo-app-elb"
                    |       |    |--ports = HTTP
                    |       |--vpc = your default vpc
                    |
                    |--LC "demo-app-lc"
                        |--t2.micro
                        |--spot
                        |--$.004
                        |--iam role: "demo-app-ec2-instance-profile"
                        |   |--Policy: "demo-app-ec2-permisions"
                        |      |--./aws-policies/codedeploy-ec2.json
                        |--user data: ./install_codedeploy.sh
```
1. if you don't already have an AWS VPC, set up a generic one in using the `Start VPC Wizard` buttong found at <https://console.aws.amazon.com/vpc/home?region=us-east-1#>
1. create a codecommit repo
    * name = demo-app
    * source = sns topic
        * new
            * name = codecommit_demo-app
            * add files = https
            * Linux
1. go to aws iam and add `AWSCodeCommitFullAccess` to the user account that will be committing code (<https://docs.aws.amazon.com/codecommit/latest/userguide/setting-up-gc.html>) OR
1. create an user in iam with permissions to perform all the following steps
    * name = demo-app-SRE
        * policies
            * ./aws-policies/code-deploy-user.json
    ```bash
    # create user policies
    arn=$(aws iam create-policy --policy-name demo-app-SRE --policy-document file://aws-policies/codedeploy-user.json --query "Policy.Arn" --output text)
    # create user and attach policies
    aws iam create-user --user-name demo-app-user1
    aws iam attach-user-policy --user-name demo-app-user --policy-arn $arn
    ```
1. upload your users public key using the `Upload SSH public key` button on the Security credential tab. (https://docs.aws.amazon.com/codecommit/latest/userguide/setting-up-ssh-unixes.html)
    * if you only have a private key, use this command to extract the public key.
    `sh-keygen -y -f ~/.ssh/userprivatekey.pem`
1. copy the `SSH key id` value
1. add the below to your ~/.ssh/config file pasting the `SSH key id`
    ```bash
    Host git-codecommit.*.amazonaws.com
    User APKAEIBAERJR2EXAMPLE
    IdentityFile ~/.ssh/userprivatekey.pem
    ```
1. ran these commands on dev box used to create repo contents
    ```bash
    git clone ssh://APKAEIBAERJR2EXAMPLE@git-codecommit.us-east-1.amazonaws.com/v1/repos/demo-app
    ```
1. copy the contents of this repo into your code commit repo
1. create an s3 bucket for deploygroup??
    * demo-app-DATE
    ```bash
    aws s3 mb s3://demo-app-$(date)
    ```
1. create sg for elb
    * name = demo-app-elb
    * ports = http
1. create elb
    * type = http https
    * name = demo-app
    * vpc = your default vpc
    * tags
        * key/value = Name/demo-app-elb
    * sg = demo-app-elb
    * target group = new
    * target name = demo-app
    * register targets = leave empty
1. create iam policies, profiles & roles
    * Role Name = demo-app-codedeploy-service-role
        * Policies
            * ./aws-policies/codedeploy-sts.json
            * AWSCodeDeployRole
    * Role Name = demo-app-ec2-instance-profile
        * Policies
            * ./aws-policies/role-policy-document.json
            * ./aws-policies/codedeploy-ec2.json
    ```bash
    # Service Role https://docs.aws.amazon.com/codedeploy/latest/userguide/getting-started-create-service-role.html
    arn=$(aws iam create-role --role-name demo-app-codedeploy-service-role --assume-role-policy-document file://aws-policies/codedeploy-sts.json --query "Role.Arn" --output text)
    aws iam attach-role-policy --role-name demo-app-codedeploy-service-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSCodeDeployRole
    # Instance Role & Profile https://docs.aws.amazon.com/codedeploy/latest/userguide/getting-started-create-iam-instance-profile.html
    aws iam create-role --role-name demo-app-ec2-instance-profile --assume-role-policy-document file://aws-policies/role-policy-document.json
    aws iam put-role-policy --role-name demo-app-ec2-instance-profile --policy-name demo-app-ec2-permissions --policy-document file://aws-policies/codedeploy-ec2.json
    aws iam create-instance-profile --instance-profile-name demo-app-ec2-instance-profile
    aws iam add-role-to-instance-profile --instance-profile-name demo-app-ec2-instance-profile --role-name demo-app-ec2-instance-profile
1. create iam role
    * name = demo-app-codedeploy
    * managed policies =
        * name = codedeploy.json
1. create security group "demo-app-elb"
    * ports = 80/tcp inbound
1. create launch config or create asg
    * ami = aws marketplace
    * search "centos" to find "CentOS 7 (x86_64) - with Updates HVM"
    * type = t2.micro
    * lc name = demo-app-lc
    * iam role = demo-app-codedeploy
    * advanced
        * user data = ./install_codedeploy.sh
        * ip = assigne public ip
    * sda1 delte on termination
    * sg = "demo-app-elb"
    * GROUP NAME = demo-app
    * size = 2
    * netwotk = your default vpc
    * subnets = your pub subs
    * keep at orig size
    * commands *replace capitalized words with your values
    * key/value  = Name/demo-app-asg
    ```bash
    imageid=$(aws ec2 describe-images --filter Name=owner-id,Values=679593333241 Name=name,Values="CentOS Linux 7 x86_64 HVM *" --query "*[].{DATE:CreationDate,ID:ImageId}" --output text | sort | cut -f2 | tail -1)
    sgid=$(aws ec2 describe-security-groups --filters Name=group-name,Values=demo-app-elb --query '*[].GroupId' --output text)

    aws autoscaling create-launch-configuration --image-id $imageid --key-name YOURAWSSSHKEYNAME --user-data file://scripts/install_codedeploy.yml --instance-type t2.micro --security-groups $sgid --block-device-mappings file://disk.yml --launch-configuration-name demo-app-lc --iam-instance-profile demo-app-ec2-instance-profile

    subnetids=( $(aws ec2 describe-subnets --filters Name=tag-value,Values=*pub* --query '*[].SubnetId' --output text) )

    aws autoscaling create-auto-scaling-group --auto-scaling-group-name demo-asg --min-size 1 --max-size 2 --launch-configuration-name demo-app-lc --vpc-zone-identifier $(echo ${subnetids[@]} | tr ' ' ',')
    ```
1. create codedeploy app <https://docs.aws.amazon.com/codedeploy/latest/userguide/getting-started-codedeploy.html>
    * name = demo-app
    * compute = ec2
    * deploy group = demo-app-east
    * deploy type = blue/green
    * env config = auto copy asg
    * asg name = demo-aapp
    * elb = demo-app
    rollback = when dep fails
    * service role arn = arn of demo-app-codedeploy-service-role created above
    ```bash
    arn=$(aws iam get-role --role-name demo-app-codedeploy-service-role --query "Role.Arn" --output text)

    aws deploy create-application --application-name demo-app
    #
    aws deploy create-deployment-group --application-name demo-pp --ec2-tag-filters Key=ec2-tag-key,Type=KEY_AND_VALUE,Value=ec2-tag-value --on-premises-tag-filters Key=on-premises-tag-key,Type=KEY_AND_VALUE,Value=on-premises-tag-value --deployment-group-name demo-DepGrp --service-role-arn $arn

    #deploy build to test new configs
    aws deploy push --application-name demo-app --s3-location s3://demo-app-<DATE>/demo-app --source .
    aws deploy create-deployment --application-name demo-app --s3-location bucket=demo-app-<DATE>,key=demo-app,bundleType=zip,eTag=FOO --deployment-group-name demo-app-east --deployment-config-name CodeDeployDefault.OneAtATime --description test-the-new-app
    ```
1. create codepipeline
    * name = demo-app
    * source = codecommit
    * repo = demo-app
    * branch = master
    * build provider = add jenkins
    * provider name = work_jenkins
    * url = blah.com
    * project name = demo-app
    * deploy provider = codedeploy
    * app name = demo-app
    * deploy group = demo-app-group
    * role name = codepipeline-service-role
    * commands (replace capitalized words in the below referenced demo-app-pipeline.json file to your unique values)
    ```bash
    aws iam create-role --role-name codepipeline-service-role --assume-role-policy-document file://aws-policies/codepipeline-service-role.json
    aws codepipeline create-pipeline --cli-input-json file://demo-app-pipeline.json
    ```

    To see how to add Slack notifications, follow SLACK.md.