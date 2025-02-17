import boto3
import botocore.exceptions
import json
import re
from .helpers import sub_json

class Secrets:
    def __init__(self, secret_name: str, region: str='eu-west-2'):
        self.client = boto3.client('secretsmanager',
                                   region_name=region)
        self.secret_name = secret_name

    def get_secrets(self):
        regex_set = [{'re_compile': re.compile(r'(?<![{}\[\]])\n'), 'replace_with': ',\n'},
                     {'re_compile': re.compile(r',(?=\s*?[{\[\]}])'), 'replace_with': ''}]
        try:
            sm_response = self.client.get_secret_value(SecretId=self.secret_name)
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'ResourceNotFoundException':
                print('ASM - ResourceNotFoundException')
            elif error.response['Error']['Code'] == 'InvalidParameterException':
                print('ASM - InvalidParameterException')
            elif error.response['Error']['Code'] == 'InvalidRequestException':
                print('ASM - InvalidRequestException')
            elif error.response['Error']['Code'] == 'DecryptionFailure':
                print('ASM - DecryptionFailure')
            elif error.response['Error']['Code'] == 'InternalServiceError':
                print('ASM - InternalServiceError')
            else:
                print('ASM - unknown error')
            raise error
        else:
            secrets = json.dumps(sm_response['SecretString'])
            secrets = json.loads(sub_json(secrets, regex_set))
            return secrets
