# SNS-to-Slack AWS Lambda Function

This is an opinionated implementation which maps an SNS topic name to a Slack channel.
It uses a single Slack webhook URL and overrides the Slack username, icon, and emoji.


## Configuration

### Create a webhook integration in your Slack account.
1. Navigate to https://<your-team-domain>.slack.com/services/new

2. Search for and select "Incoming WebHooks".

3. Choose the default channel where messages will be sent and click "Add Incoming WebHooks Integration".

4. Copy the webhook URL from the setup instructions and use it in the next section.

5. Name the integration something meaningful like *AWS Lambda sns-to-slack*.

### Encrypt Slack webhook URL with KMS key
1. Create a KMS key - http://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html.

2. Encrypt the event collector token using the AWS CLI.
```shell
    $ aws kms encrypt --key-id alias/<KMS key name> --plaintext "<SLACK_HOOK_URL>"
```

Note: You must exclude the protocol from the URL (e.g. "hooks.slack.com/services/abc123").

3. Copy the base-64 encoded, encrypted key (CiphertextBlob) and add it to the `encrypted_webhook_url` key in the next section.

### This project's configuration file

Copy `config.json.example` to `config.json` and update the `encrypted_webhook_url` key to the encrypted Slack URL that you copied above.

### Create your Slack channels

Slack channels have a limit of 21 characters.
You'll want to namespace your channels accordingly.
`channel_map` setting is the mapping from the SNS topic name to the channel name.


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

### Create the SNS-to-Slack Lambda function

You can do all of this via the AWS Lambda console, but if you are more automation oriented a rough outline of steps follows:

#### Lambda IAM Role for execution

The Lambda function requires an IAM Role to execute.
You can create this in the AWS IAM console or the AWS CLI.

```shell
$ aws iam create-role --role-name lambda_basic_execution --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'
```

#### IAM Role Policy

To permit the IAM Role above to execute and put logs in CloudWatch Logs:

```shell
aws iam put-role-policy --role-name lambda_basic_execution --policy-name lambda_basic_execution --policy-document '{
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
}'
```


The Role name `lambda_basic_execution` is created by the AWS Lambda console.

The ARN: *arn:aws:iam::<AWS_ACCOUNT_ID>:role/lambda_basic_execution*

#### Create a .zip file of SNS-to-Slack for upload to Lambda

If you using a virtualenv (you should), then the following command will upload a .zip file of the SNS-to-Slack Lambda function using the AWS CLI and a credential profile named `my_profile`:

```shell
zip -u sns-to-slack.zip lambda_function.py config.json
pushd $VIRTUAL_ENV/lib/python2.7/site-packages
zip -u -r $OLDPWD/sns-to-slack.zip . --exclude pip\* --exclude setuptools\*
popd
```

#### Create the function with the AWS CLI

```shell
aws lambda create-function \
 --function-name sns-to-slack \
 --runtime python2.7 \
 --role arn:aws:iam::<AWS_ACCOUNT_ID>:role/lambda_basic_execution \
 --handler lambda_function.lambda_handler \
 --zip-file fileb://./sns-to-slack.zip \
 --description "Send SNS events to Slack" \
 --memory-size 128 \
 --timeout 3
 ```

### Update an existing Lambda function

```shell
aws lambda update-function-code \
  --function-name function:sns-to-slack \
  --zip-file fileb://./sns-to-slack.zip
```


### Create version aliases for development, test, staging, production, etc

```shell
aws lambda create-alias \
  --function-name sns-to-slack \
  --description "development version" \
  --function-version "\$LATEST" \
  --name development
```

```shell
aws lambda publish-version \
  --function-name sns-to-slack
```

### Lambda Resources
https://docs.aws.amazon.com/lambda/latest/dg/python-lambda.html
https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html
https://docs.aws.amazon.com/lambda/latest/dg/versioning-aliases.html
