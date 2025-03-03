import os
import json
import requests
import boto3
from datetime import datetime
from decimal import Decimal

# Read configuration from environment variables
S3_BUCKET = os.environ.get("S3_BUCKET", "ecfr-analyzer-data-5655123")
DYNAMO_TABLE = os.environ.get("DYNAMO_TABLE", "ECFRAnalysis")

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Custom JSON encoder for Decimal values
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
    except Exception as e:
        print("Error serializing event:", str(e))
    
    http_method = event.get("httpMethod", "")
    
    # Handle CORS preflight request
    if http_method == "OPTIONS":
        print("Processing OPTIONS request")
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": ""
        }
    
    # Handle POST request
    if http_method == "POST":
        try:
            body = json.loads(event.get("body", "{}"))
        except Exception as e:
            print("Error parsing request body:", str(e))
            body = {}
        
        action = body.get("action", "refresh")
        print("Action requested:", action)
        
        if action == "full_refresh":
            agencies = fetch_all_data("/api/admin/v1/agencies.json")
            search_counts = fetch_all_data("/api/search/v1/count")
            analysis_data = {
                "agencies": agencies,
                "search_counts": search_counts,
                "custom_metric": compute_custom_metric(agencies, search_counts)
            }
        elif action == "detailed":
            analysis_data = {"detailed_data": fetch_all_data("/api/search/v1/results")}
        else:
            analysis_data = {"agencies": fetch_all_data("/api/admin/v1/agencies.json")}
        
        print("Final analysis data:", analysis_data)
        
        # Convert floats to Decimal (if needed) for DynamoDB, but then use a custom encoder for S3
        analysis_data_for_dynamodb = convert_floats_to_decimal(analysis_data)
        
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        s3_key = f"analysis/{timestamp}.json"
        
        try:
            print(f"Writing analysis results to S3 bucket {S3_BUCKET} with key {s3_key}")
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=json.dumps(analysis_data, cls=DecimalEncoder),
                ContentType='application/json'
            )
            print("Successfully wrote to S3")
        except Exception as e:
            error_msg = f"Error writing to S3: {str(e)}"
            print(error_msg)
            return {
                "statusCode": 500,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps(error_msg)
            }
        
        try:
            table = dynamodb.Table(DYNAMO_TABLE)
            item = {
                "id": timestamp,
                "action": action,
                "results": analysis_data_for_dynamodb,
                "timestamp": timestamp
            }
            print(f"Writing item to DynamoDB table {DYNAMO_TABLE}: {item}")
            table.put_item(Item=item)
            print("Successfully wrote to DynamoDB")
        except Exception as e:
            error_msg = f"Error writing to DynamoDB: {str(e)}"
            print(error_msg)
            return {
                "statusCode": 500,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps(error_msg)
            }
        
        return {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({
                "message": "Data fetched and processed successfully",
                "s3_key": s3_key,
                "timestamp": timestamp,
                "action": action
            })
        }
    
    print("Unsupported HTTP method:", http_method)
    return {
        "statusCode": 400,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps("Bad Request")
    }

def fetch_all_data(endpoint):
    base_url = "https://www.ecfr.gov"
    url = base_url + endpoint
    results = []
    while url:
        print("Fetching URL:", url)
        try:
            response = requests.get(url)
            print("Response status:", response.status_code)
            response.raise_for_status()
            data = response.json()
            page_data = data.get("results") or data.get("agencies") or data
            if isinstance(page_data, list):
                results.extend(page_data)
            else:
                results.append(page_data)
            next_url = data.get("next")
            if next_url:
                url = base_url + next_url if not next_url.startswith("http") else next_url
            else:
                url = None
        except Exception as e:
            print("Error fetching data:", str(e))
            break
    print(f"Total items fetched from {endpoint}: {len(results)}")
    return results

def convert_floats_to_decimal(obj):
    """Recursively convert floats in the object to Decimal for DynamoDB storage."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(i) for i in obj]
    else:
        return obj

def compute_custom_metric(agencies, search_counts):
    total_agencies = len(agencies) if isinstance(agencies, list) else 0
    total_search = len(search_counts) if isinstance(search_counts, list) else 0
    return {"combined_total": total_agencies + total_search}