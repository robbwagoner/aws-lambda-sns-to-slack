#!/usr/bin/env python
'''
Parse an SNS event message and send to a Slack Channel
'''
from __future__ import print_function

import json
import re

import requests

__author__ = "Robb Wagoner (@robbwagoner)"
__copyright__ = "Copyright 2015 Robb Wagoner"
__credits__ = ["Robb Wagoner"]
__license__ = "Apache License, 2.0"
__version__ = "0.1.0"
__maintainer__ = "Robb Wagoner"
__email__ = "robb.wagoner+github@gmail.com"
__status__ = "Production"

def get_slack_emoji(event_type):
    '''Map an event type to an emoji
    '''
    emoji_map = {
        'alerts': ':fire:'}
    try:
        return emoji_map[event_type]
    except KeyError:
        return ':mantelpiece_clock:'

def get_slack_username(event_source):
    '''Map event source to the Slack username
    '''
    username_map = {
        'cloudwatch': 'AWS CloudWatch',
        'autoscaling': 'AWS AutoScaling',
        'elasticache': 'AWS ElastiCache' }
    try:
        return username_map[event_source]
    except KeyError:
        return 'AWS Lambda'

def get_slack_channel(region, event_env, event_type):
    '''Map region and event type to Slack channel name
    '''
    channel_map = {
        'production': {
            'alerts': '#alerts-{}'.format(region),
            'events': '#events-{}'.format(region) },
        'staging': {
            'alerts': '#alerts-staging-{}'.format(region),
            'events': '#events-staging-{}'.format(region) } }
    try:
        return channel_map[event_env][event_type]
    except KeyError:
        return '#events-{region}'.format(region=region)

def autoscaling_capacity_change(cause):
    '''
    '''
    s = re.search(r'capacity from (\w+ to \w+)', cause)
    if s:
        return s.group(0)
    else:
        return '--'

def lambda_handler(event, context):
    '''The Lambda function handler
    '''
    with open('config.json') as f:
        config = json.load(f)
    
    sns = event['Records'][0]['Sns']
    print('DEBUG:', sns['Message'])
    json_msg = json.loads(sns['Message'])

    if sns['Subject']:
        message = sns['Subject']
    else:
        message = sns['Message']

    # https://api.slack.com/docs/attachments
    attachments = []
    if json_msg.get('AlarmName'):
        event_source = 'cloudwatch'
        color_map = {
            'OK': 'good',
            'INSUFFICIENT_DATA': 'warning',
            'ALARM': 'danger'
        }
        attachments = [{
            'fallback': json_msg,
            'message': json_msg,
            'color': color_map[json_msg['NewStateValue']],
            "fields": [{
              "title": "Alarm",
              "value": json_msg['AlarmName'],
              "short": True
            }, {
              "title": "Status",
              "value": json_msg['NewStateValue'],
              "short": True
            }, {
              "title": "Reason",
              "value": json_msg['NewStateReason'],
              "short": False
            }]
        }]
    elif json_msg.get('Cause'):
        event_source = 'autoscaling'
        attachments = [{
            "text": "Details",
            "fallback": message,
            "color": "good",
            "fields": [{
              "title": "Capacity Change",
              "value": autoscaling_capacity_change(json_msg['Cause']),
              "short": True
            }, {
              "title": "Event",
              "value": json_msg['Event'],
              "short": False
            }, {
              "title": "Cause",
              "value": json_msg['Cause'],
              "short": False
            }]
        }]
    elif json_msg.get('ElastiCache:SnapshotComplete'):
        event_source = 'elasticache'
        attachments = [{
            "text": "Details",
            "fallback": message,
            "color": "good"
        }]
    else:
        event_source = 'other' 

    # SNS Topic Names => Slack Channels
    #  <env>-alerts => alerts-<region>
    #  <env>-notices => events-<region>
    topic_name = sns['TopicArn'].split(':')[-1]
    event_env = topic_name.split('-')[0]
    event_type = topic_name.split('-')[-1]
    region = sns['TopicArn'].split(':')[3]

    print('DEBUG:',topic_name,event_type,region)

    payload = {
        'text': message,
        'channel': get_slack_channel(region, event_env, event_type), 
        'username': get_slack_username(event_source), 
        'icon_emoji': get_slack_emoji(event_type) }
    if attachments:
        payload['attachments'] = attachments
    print('DEBUG:', payload)
    r = requests.post(config['slack_webhook_url'], json=payload)
    return r.status_code

# Test locally
if __name__ == '__main__':
    sns_event_template = json.loads(r"""
{
  "Records": [
    {
      "EventVersion": "1.0",
      "EventSubscriptionArn": "arn:aws:sns:EXAMPLE",
      "EventSource": "aws:sns",
      "Sns": {
        "SignatureVersion": "1",
        "Timestamp": "1970-01-01T00:00:00.000Z",
        "Signature": "EXAMPLE",
        "SigningCertUrl": "EXAMPLE",
        "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
        "Message": "{\"AlarmName\":\"sns-slack-test-from-cloudwatch-total-cpu\",\"AlarmDescription\":null,\"AWSAccountId\":\"259222253036\",\"NewStateValue\":\"OK\",\"NewStateReason\":\"Threshold Crossed: 1 datapoint (7.9053535353535365) was not greater than or equal to the threshold (8.0).\",\"StateChangeTime\":\"2015-11-09T21:19:43.454+0000\",\"Region\":\"US - N. Virginia\",\"OldStateValue\":\"ALARM\",\"Trigger\":{\"MetricName\":\"CPUUtilization\",\"Namespace\":\"AWS/EC2\",\"Statistic\":\"AVERAGE\",\"Unit\":null,\"Dimensions\":[],\"Period\":300,\"EvaluationPeriods\":1,\"ComparisonOperator\":\"GreaterThanOrEqualToThreshold\",\"Threshold\":8.0}}",
        "MessageAttributes": {
          "Test": {
            "Type": "String",
            "Value": "TestString"
          },
          "TestBinary": {
            "Type": "Binary",
            "Value": "TestBinary"
          }
        },
        "Type": "Notification",
        "UnsubscribeUrl": "EXAMPLE",
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:staging-notices",
        "Subject": "OK: sns-slack-test-from-cloudwatch-total-cpu"
      }
    }
  ]
}""")
    print('running locally')
    print(lambda_handler(sns_event_template,None))

