# SNS-to-Slack AWS Lambda Function

This is an opinionated implementation which maps an SNS topic name to a Slack channel.
It uses a single Slack webhook URL and overrides the Slack username, icon, and emoji.


## Configuration

### Slack
Create a webhook integration in your Slack account.
Name the integration something meaningful like *AWS Lambda sns-to-slack*.
Copy the *Webhook URL* for the integration you just created.

### This project's configuration file

Copy `config.json.example` to `config.json` and update the `slack_webhook_url` key to the Slack integration URL that you copied above.

### Create your Slack channels

Slack channels have a limit of 21 characters.
You'll want to namespace your channels accordingly.
At the moment the SNS topic name maps to the Slack channel name.
I intend to change this behavior.
In the meantime, however the mapping is this:

| SNS topic name | Slack channel name |
| --- | --- |
| `production-alerts` | `#alerts-<AWS_REGION>` |
| `production-events` | `#events-<AWS_REGION>` |


### Emoji

* Alerts get the :fire: `:fire:` emoji.
* Events get the :mantelpiece_clock: `:mantelpiece_clock:` emoji.

I will be changing this to me more configurable, too.

## Development and testing locally

There are [some](https://github.com/HDE/python-lambda-local) Pythonic ways of developing and testing AWS Lambda functions locally, but I haven't used them (yet).
In the meantime, a simplistic test is:

```shell
python lambda_function.py
```

The Lambda Function can be named whatever you like. 
Installing/updating the Lambda Function can be done using the AWS CLI.
There are [more](https://github.com/gene1wood/cfnlambda) [Pythonic](https://github.com/PitchBook/pylambda) ways of doing so however.

### Copy .zip file to S3

If you using a virtualenv (you should), then the following command will upload a .zip file of the SNS-to-Slack Lambda function using the AWS CLI and a credential profile named `my_profile`:

```shell
zip -u ~/sns-to-slack.zip lambda_function.py config.json
pushd $VIRTUAL_ENV/lib/python2.7/site-packages
zip -u -r ~/sns-to-slack.zip .
popd
aws --profile my_profile s3 cp ~/sns-to-slack.zip s3://my-lambda-us-east-1/
```

### Create the SNS-to-Slack Lambda function

You can do all of this via the AWS Lambda console, but if you are more automation oriented a rough outline of steps follows:

#### Lambda IAM Role for execution

The Lambda function requires an IAM Role to execute. 
You can create this in the AWS IAM console or the AWS CLI. 
I leave that to the viewer.
The Role name `lambda_basic_execution` is created by the AWS Lambda console. 

The ARN: *arn:aws:iam::<AWS_ACCOUNT_ID>:role/lambda_basic_execution*

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```
#### Create the function with the AWS CLI

```shell
aws lambda create-function \
 --profile my_profile \
 --function-name sns-to-slack \
 --runtime python \
 --role lambda_basic_execution \
 --handler lambda_function.lambda_handler \
 --zip-file ~/sns-to-slack.zip \
 --description "Send SNS events to Slack"
 ```

### Update an existing Lambda function

```shell
aws lambda update-function-code \
  --profile my_profile \
  --region us-east-1 \
  --function-name arn:aws:lambda:us-east-1:<AWS_ACCOUNT_ID>:function:sns-to-slack \
  --s3-bucket my-lambda-us-east-1 \
  --s3-key sns-to-slack.zip
```

### Lambda Resources
https://docs.aws.amazon.com/lambda/latest/dg/python-lambda.html
https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html
https://docs.aws.amazon.com/lambda/latest/dg/versioning-aliases.html
