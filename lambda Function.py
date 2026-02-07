import boto3
import json
from datetime import datetime

ec2 = boto3.client('ec2')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

TABLE_NAME = 'EBSConversionLogs'
SNS_TOPIC_ARN = 'arn:aws:sns:ap-south-1:906510884898:EBS-Volume-Notification'

table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    try:
        # Describe all EBS volumes
        response = ec2.describe_volumes()
        
        for volume in response['Volumes']:
            volume_id = volume['VolumeId']
            volume_type = volume['VolumeType']
            size = volume['Size']
            region = ec2.meta.region_name

            # Check AutoConvert tag
            tags = volume.get('Tags', [])
            auto_convert = any(
                tag['Key'] == 'AutoConvert' and tag['Value'].lower() == 'true'
                for tag in tags
            )

            # Convert only gp2 volumes with AutoConvert=true
            if volume_type == 'gp2' and auto_convert:
                timestamp = datetime.utcnow().isoformat()

                # Log to DynamoDB
                table.put_item(
                    Item={
                        'VolumeId': volume_id,
                        'Timestamp': timestamp,
                        'OldType': 'gp2',
                        'NewType': 'gp3',
                        'Size': size,
                        'Region': region,
                        'Status': 'INITIATED'
                    }
                )

                # Modify volume to gp3
                ec2.modify_volume(
                    VolumeId=volume_id,
                    VolumeType='gp3'
                )

                # Send SNS notification
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject='EBS Volume Converted',
                    Message=(
                        f"EBS Volume Conversion Successful\n\n"
                        f"Volume ID: {volume_id}\n"
                        f"Old Type: gp2\n"
                        f"New Type: gp3\n"
                        f"Size: {size} GiB\n"
                        f"Region: {region}\n"
                        f"Time: {timestamp}"
                    )
                )

        return {
            'statusCode': 200,
            'body': json.dumps('EBS volume optimization completed successfully')
        }

    except Exception as e:
        print("Error:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
