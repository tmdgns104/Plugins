import boto3
from datetime import datetime

class CloudWatchUtils:
    def __init__(self, region_name, aws_access_key=None, aws_secret_key=None):
        if aws_access_key and aws_secret_key:
            self.cloudwatch = boto3.client(
                'cloudwatch',
                region_name=region_name,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
            self.logs = boto3.client(
                'logs',
                region_name=region_name,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
        else:
            self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
            self.logs = boto3.client('logs', region_name=region_name)

    def get_metric_data(self, namespace, metric_name, dimensions, start_time, end_time, period=300, stat='Average'):
        try:
            response = self.cloudwatch.get_metric_data(
                MetricDataQueries=[
                    {
                        'Id': 'metric_query',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': namespace,
                                'MetricName': metric_name,
                                'Dimensions': dimensions,
                            },
                            'Period': period,
                            'Stat': stat
                        },
                        'ReturnData': True
                    },
                ],
                StartTime=start_time,
                EndTime=end_time
            )

            results = []
            for result in response['MetricDataResults']:
                results.append({
                    'Id': result['Id'],
                    'Timestamps': result['Timestamps'],
                    'Values': result['Values']
                })

            return results
        except Exception as e:
            print(f"Error fetching metric data: {e}")
            return []

    def get_logs(self, log_group_name, log_stream_name, start_from_head=True):
        try:
            response = self.logs.get_log_events(
                logGroupName=log_group_name,
                logStreamName=log_stream_name,
                startFromHead=start_from_head
            )

            events = []
            for event in response['events']:
                events.append({
                    'Timestamp': event['timestamp'],
                    'Message': event['message']
                })

            return events
        except Exception as e:
            print(f"Error fetching log events: {e}")
            return []

    def list_log_streams(self, log_group_name):
        try:
            response = self.logs.describe_log_streams(logGroupName=log_group_name)
            return [stream['logStreamName'] for stream in response['logStreams']]
        except Exception as e:
            print(f"Error fetching log streams: {e}")
            return []