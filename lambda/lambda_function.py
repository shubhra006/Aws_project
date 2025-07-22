import json
import boto3
import base64
import hashlib
import uuid

# AWS setup
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('secret006')
bucket = boto3.client('s3')
bucket_name = 'secret006'  # Replace with your actual bucket name

# Hashing function
def hash_password(p):
    return hashlib.sha256(p.encode('utf-8')).hexdigest()

# Response helper
def response(status, body):
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }

# Lambda main handler
def lambda_handler(event, context):
    method = event['httpMethod']
    if method == 'POST':
        return add(event)
    if method == 'GET':
        return get(event)
    return response(405, 'Method not allowed')

# Add image and data
def add(event):
    try:
        body = json.loads(event['body'])
        id = body.get('id') or str(uuid.uuid4())
        image = body.get('image')
        password = body.get('password')

        if not id or not password:
            return response(400, 'id and password required')

        hashed_password = hash_password(password)
        key = f'photo/{id}.jpg'

        image_url = ''
        if image and ',' in image:
            image_data = base64.b64decode(image.split(',')[1])
            bucket.put_object(Body=image_data, Bucket=bucket_name, Key=key, ContentType='image/jpeg')
            image_url = f'https://{bucket_name}.s3.amazonaws.com/{key}'

        product = {
            'id': id,
            'image_url': image_url,
            'password': hashed_password
        }

        table.put_item(Item=product)
        return response(200, 'Item added successfully')

    except Exception as e:
        return response(400, f'Error: {str(e)}')

# Get image by ID and password
def get(event):
    try:
        p = event.get('queryStringParameters') or {}
        id = p.get('id')
        password = p.get('password')

        if not id or not password:
            return response(400, 'id and password required')

        r = table.get_item(Key={'id': id})
        item = r.get('Item')

        if not item:
            return response(404, 'Item not found')

        if item['password'] != hash_password(password):
            return response(403, 'Invalid password')

        return response(200, item['image_url'])

    except Exception as e:
        return response(400, f'Error: {str(e)}')

