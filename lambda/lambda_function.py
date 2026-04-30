import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal

ce = boto3.client('ce')
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')

table = dynamodb.Table('cost_table')

THRESHOLD = 1  # USD (keep low for testing)
import os
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': str(yesterday),
            'End': str(today)
        },
        Granularity='DAILY',
        Metrics=['UnblendedCost']
    )

    cost = Decimal(response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])
    cloudwatch.put_metric_data(
    Namespace='CostMonitoring',
    MetricData=[
        {
            'MetricName': 'DailyCost',
            'Value': float(cost),
            'Unit': 'None'
        }
    ]
)

    print(f"Cost for {yesterday}: {cost}")

    # Store in DynamoDB
    table.put_item(
        Item={
            'date': str(yesterday),
            'cost': cost
        }
    )

    # Send alert if threshold crossed
    if cost > THRESHOLD:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=f"AWS cost exceeded threshold! Cost: ${cost}",
            Subject="AWS Cost Alert"
        )
        print("Alert sent!")

    return {
        "statusCode": 200,
        "body": json.dumps(f"Cost: {cost}")
    }
