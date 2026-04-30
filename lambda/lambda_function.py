import json
import time
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('rate_limit_table')

cloudwatch = boto3.client('cloudwatch')

# CONFIG
RATE = 5          # tokens per minute
CAPACITY = 10     # burst capacity

def lambda_handler(event, context):
    api_key = event['headers'].get('x-api-key', 'anonymous')
    now = int(time.time())

    response = table.get_item(Key={'api_key': api_key})

    if 'Item' in response:
        item = response['Item']
        tokens = item['tokens']
        last_refill = item['last_refill_time']

        # refill tokens
        elapsed = now - last_refill
        refill = (elapsed * RATE) / 60
        tokens = min(CAPACITY, tokens + refill)
    else:
        tokens = CAPACITY

    print(f"API Key: {api_key}")
    print(f"Tokens before check: {tokens}")

    # ❌ BLOCKED
    if tokens < 1:
        cloudwatch.put_metric_data(
            Namespace='RateLimiter',
            MetricData=[
                {
                    'MetricName': 'BlockedRequests',
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
        )

        print("Request blocked")

        return {
            "statusCode": 429,
            "body": json.dumps("Rate limit exceeded")
        }

    # ✅ ALLOWED
    tokens -= 1

    table.put_item(
        Item={
            'api_key': api_key,
            'tokens': tokens,
            'last_refill_time': now
        }
    )

    cloudwatch.put_metric_data(
        Namespace='RateLimiter',
        MetricData=[
            {
                'MetricName': 'AllowedRequests',
                'Value': 1,
                'Unit': 'Count'
            }
        ]
    )

    print(f"Request allowed, tokens left: {tokens}")

    return {
        "statusCode": 200,
        "body": json.dumps("Request allowed")
    }
