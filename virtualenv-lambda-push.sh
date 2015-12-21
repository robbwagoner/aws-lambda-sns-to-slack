#!/bin/bash
#
# Required environment variables:
#   AWS_ACCOUNT_ID
# Recommended environment variables:
#   AWS_REGION
#   AWS_PROFILE
#
set -x
zip -u sns-to-slack.zip lambda_function.py config.json
pushd $VIRTUAL_ENV/lib/python2.7/site-packages
zip -u -r $OLDPWD/sns-to-slack.zip . \
  --exclude pip\* \
  --exclude setuptools\* \
  --exclude virtualenv\*
popd

case $1 in 
  ( create )
    aws lambda create-function \
     --function-name sns-to-slack \
     --runtime python2.7 \
     --role arn:aws:iam::$AWS_ACCOUNT_ID:role/lambda_basic_execution \
     --handler lambda_function.lambda_handler \
     --zip-file fileb://./sns-to-slack.zip \
     --description "Send SNS events to Slack" \
     --memory-size 128 \
     --timeout 3
    ;;
  ( update )
    aws lambda update-function-code \
      --function-name function:sns-to-slack \
      --zip-file fileb://./sns-to-slack.zip
    ;;
  ( * )
    echo "USAGE: $0 [create|update]" 1>&2
    exit 255
    ;;
esac
