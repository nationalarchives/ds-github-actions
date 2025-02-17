import boto3
import botocore.exceptions
from .helpers import set_random_id


class SQSHandler:
    def __init__(self, queue_name, queue_owner, region: str='eu-west-2'):
        self.client = boto3.client('sqs',
                                   region_name=region)
        self.queue_name = queue_name
        self.queue_owner = queue_owner
        self.queue_client = boto3.client('sqs',
                                         region_name=region)
        self.queue_url = self.get_queue_url()
        self.client.set_queue_attributes(QueueUrl=self.queue_url,
                                         Attributes={'ReceiveMessageWaitTimeSeconds': '20'})

    def get_queue_url(self):
        try:
            response = self.client.get_queue_url(QueueName=self.queue_name,
                                                 QueueOwnerAWSAccountId=self.queue_owner)
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'RequestThrottled ':
                print('SQS - RequestThrottled')
            elif error.response['Error']['Code'] == 'QueueDoesNotExist ':
                print('SQS - QueueDoesNotExist')
            elif error.response['Error']['Code'] == 'InvalidAddress ':
                print('SQS - RequestThrottled')
            elif error.response['Error']['Code'] == 'InvalidSecurity ':
                print('SQS - InvalidSecurity')
            elif error.response['Error']['Code'] == 'UnsupportedOperation ':
                print('SQS - UnsupportedOperation')
            else:
                print('SQS - unknown error')
            raise error
        else:
            return response['QueueUrl']

    def get_attributes(self):
        return self.client.get_queue_attributes(QueueUrl=self.queue_url,
                                                AttributeNames=['All'])

    def receive_message(self, max_number: int = 1):
        attempt_id = set_random_id()
        try:
            response = self.client.receive_message(
                QueueUrl=self.queue_url,
                AttributeNames=[
                    'SentTimestamp'
                ],
                MaxNumberOfMessages=max_number,
                MessageSystemAttributeNames=[
                    'All'
                ],
                ReceiveRequestAttemptId=attempt_id,
                WaitTimeSeconds=20
            )
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'UnsupportedOperation ':
                print('SQS - UnsupportedOperation')
            elif error.response['Error']['Code'] == 'OverLimit ':
                print('SQS - OverLimit')
            elif error.response['Error']['Code'] == 'RequestThrottled ':
                print('SQS - RequestThrottled')
            elif error.response['Error']['Code'] == 'QueueDoesNotExist ':
                print('SQS - QueueDoesNotExist')
            elif error.response['Error']['Code'] == 'InvalidSecurity ':
                print('SQS - InvalidSecurity')
            elif error.response['Error']['Code'] == 'InvalidAddress ':
                print('SQS - InvalidAddress')
            else:
                print('SQS - unknown error')
            raise error
        else:
            return response

    def delete_message(self, handle: str) -> None:
        try:
            self.client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=handle
            )
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'InvalidIdFormat ':
                print('SQS - InvalidIdFormat')
            elif error.response['Error']['Code'] == 'ReceiptHandleIsInvalid ':
                print('SQS - ReceiptHandleIsInvalid')
            elif error.response['Error']['Code'] == 'RequestThrottled ':
                print('SQS - RequestThrottled')
            elif error.response['Error']['Code'] == 'QueueDoesNotExist ':
                print('SQS - QueueDoesNotExist')
            elif error.response['Error']['Code'] == 'UnsupportedOperation ':
                print('SQS - UnsupportedOperation')
            elif error.response['Error']['Code'] == 'InvalidSecurity ':
                print('SQS - InvalidSecurity')
            elif error.response['Error']['Code'] == 'InvalidAddress ':
                print('SQS - InvalidAddress')
            else:
                print('SQS - unknown error')
            raise error
