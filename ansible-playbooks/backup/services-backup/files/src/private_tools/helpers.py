import math
import random
import string
import re
import boto3
import botocore.exceptions
import json
from datetime import datetime
from datetime import timedelta

def size_converter(value: int = 0, start: str = 'B', end: str = 'GB', precision: int = 2, long_names: bool = False,
                   base: int = 1024):
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    units_long = ['Byte', 'Kilobyte', 'Megabyte', 'Gigabyte', 'Terabyte', 'Petabyte', 'Exabyte', 'Zettabyte',
                  'Yottabyte']
    start_index = units.index(start.upper())
    end_index = units.index(end.upper())
    if start_index == end_index:
        if start == 'B':
            output_unit = start.upper() if not long_names else ' ' + units_long[start_index]
            return '{:d}{unit}'.format(value, unit=output_unit)
        else:
            output_unit = start.upper() if not long_names else ' ' + units_long[start_index]
            return '{:.{precision}f}{unit}'.format(value, precision=precision, unit=output_unit)
    elif start_index < end_index:
        result = value / pow(base, (end_index - start_index))
        output_unit = end.upper() if not long_names else ' ' + units_long[end_index]
        return '{:.{precision}f}{unit}'.format(result, precision=precision, unit=output_unit)
    elif start_index > end_index:
        output_unit = start.upper() if not long_names else ' ' + units_long[start_index]
        result = value * pow(base, (start_index - end_index))
        return '{:.{precision}f}{unit}'.format(result, precision=precision, unit=output_unit)
    else:
        return "n/a"


def set_random_id(length: int = 64):
    random.seed()
    return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(length))


def find_key_dict(k: str, a: dict = {}):
    k = k.casefold()
    for key in a:
        if key in k:
            return key
    return None


def find_value_dict(k: str, a: dict = {}):
    k = k.casefold()
    for key in a:
        if key.casefold() == k:
            return a[key]
    return None


def sub_json(text: str, re_set):
    prepared_dict = text
    for step in re_set:
        prepared_dict = re.sub(step['re_compile'], step['replace_with'], prepared_dict)
    return prepared_dict


def deconstruct_path(object_key):
    if object_key.startswith('/'):
        object_key = object_key[1:]
    path_elements = object_key.split('/')
    object_name = path_elements[-1]
    location_filters = []
    if len(path_elements) > 1:
        ap_name = path_elements[0]
        location = "/".join(path_elements[:-1])
        for x in range(1, len(path_elements)+1):
            location_filters.append("/".join(path_elements[0:x]))
    else:
        ap_name = ''
        location = ''
    return {'object_key': object_key, 'object_name': object_name,
            'access_point': ap_name, 'location': location, 'location_filters': location_filters}


def get_ssm_parameters(name: str, aws_region: str):
    params = {}
    regex_line = re.compile(r'(?<![{}\[\]])\n')
    regex_comma = re.compile(r',(?=\s*?[{\[\]}])')
    regex_set = [{'re_compile': regex_line, 'replace_with': ',\n'},
                 {'re_compile': regex_comma, 'replace_with': ''}]
    client = boto3.client('ssm',
                          region_name=aws_region)
    try:
        response = client.get_parameter(Name=name)
    except botocore.exceptions.ClientError as error:
        raise error
    # why twice json.loads????? Is this modern python?
    values = json.loads(json.loads(sub_json(json.dumps(response['Parameter']['Value']), regex_set)))
    for k, v in values.items():
        params.update({k: v})
    return params


def get_asm_parameters(name: str, aws_region: str) -> json:
    client = boto3.client('secretsmanager',
                          region_name=aws_region)

    try:
        secrets = client.get_secret_value(SecretId=name)
    except botocore.exceptions.ClientError as error:
        raise error
    return secrets["SecretString"]


def create_upload_map(total_size: int):
    upload_map = []
    if total_size < 104857601:
        # up to 100MB - set part size to 5MB
        block_size = 5242880
    elif total_size < 1073741825:
        # up to 1GB - set part size to 100MB
        block_size = 104857600
    elif total_size < 53687091201:
        # up to 50GB - set part size to 200MB
        block_size = 214748365
    elif total_size < 107374182401:
        # up to 100GB - set part size to 410MB
        block_size =  429496730
    elif total_size < 1099511627778:
        # up to 1TB - set part size to 4GB
        block_size =  4398046512
    elif total_size < 2748779069441:
        # up to 2.5TB - set part size to 10GB
        block_size = 10995116278
    else:
        block_size = 10995116278
    part_count = math.ceil(-(-total_size / block_size))
    low_part_count = math.floor(-(-total_size / block_size))
    last_part_size = total_size - (low_part_count * block_size)
    if part_count <= 1:
        upload_map = [[0, (total_size - 1), total_size]]
    else:
        transfer_total = 0
        last_part_no = part_count - 1
        range_from = 0
        range_to = 0
        for i in range(part_count):
            if i == last_part_no:
                transfer_size = last_part_size
                range_to = range_from + transfer_size - 1
                transfer_total += transfer_size
            else:
                range_to = range_from + block_size - 1
                transfer_total += block_size
                transfer_size = block_size
            upload_map.append([range_from, range_to, transfer_size])
            range_from = range_to + 1
    return upload_map


def process_obj_name(name: str, add_ts: int = 1):
    if add_ts == 1:
        tn_split = name.split('.')
        if len(tn_split) > 1:
            target_name = f'{".".join(tn_split[:-1])}_{str(datetime.now().timestamp()).replace(".", "_")}.{"".join(tn_split[-1:])}'
        else:
            target_name = f'{name}_{str(datetime.now().timestamp()).replace(".", "_")}'
    else:
        target_name = name
    return target_name


def calc_timedelta(timevalue):
    end = None
    if timevalue is not None:
        today = datetime.now()
        nd = None
        if timevalue[0].lower() == 'd':
            nd = today + timedelta(days=int(timevalue[1:]))
        elif timevalue[0].lower() == 'm':
            nd = today + timedelta(days=int(timevalue[1:]) * 7)
        elif timevalue[0].lower() == 'm':
            nd = today + timedelta(days=int(timevalue[1:]) * 30)
        elif timevalue[0].lower() == 'y':
            nd = today + timedelta(days=int(timevalue[1:]) * 365)
        if nd is not None:
            end = datetime(int(nd.strftime('%Y')), int(nd.strftime('%m')), int(nd.strftime('%d'))).strftime('%Y-%m-%d %H:%M:%S')
    return end


def extract_checksum_details(dataset: dict = None):
    if dataset is not None:
        if 'ChecksumCRC32' in dataset:
            return {'checksum_encoding': 'ChecksumCRC32', 'checksum': dataset['ChecksumCRC32']}
        if 'ChecksumCRC32C' in dataset:
            return {'checksum_encoding': 'ChecksumCRC32C', 'checksum': dataset['ChecksumCRC32C']}
        if 'ChecksumSHA1' in dataset:
            return {'checksum_encoding': 'ChecksumSHA1', 'checksum': dataset['ChecksumSHA1']}
        if 'ChecksumSHA256' in dataset:
            return {'checksum_encoding': 'ChecksumSHA256', 'checksum': dataset['ChecksumSHA256']}
        if 'ChecksumCRC64NVME' in dataset:
            return {'checksum_encoding': 'ChecksumCRC64NVME', 'checksum': dataset['ChecksumCRC64NVME']}
    return None
