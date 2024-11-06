import boto3
import json
import requests
import shutil
import os
import multiprocessing as mp
from pathlib import Path
from datetime import datetime
from multiprocessing import Process, Queue, current_process
from private_tools import sha256sum, sha1sum, rmdir, s3_folder_exists, get_asm_parameter


def get_repos(tasks, done, pdata):
    entry = tasks.get()
    archive_name = f'{entry["name"]}.zip'
    repo_counters = {'private': 0,
                     'public': 0,
                     'internal': 0,
                     'error': 0}

    if entry['private']:
        url_parts = entry['clone_url'].split('//')
        github_creds = f'{pdata["repo_login"]["user"]}:{pdata["repo_login"]["token"]}@'
        repo_url = f'{url_parts[0]}//{github_creds}{url_parts[1]}'
        repo_counters['private'] += 1
    elif entry['internal']:
        repo_url = entry['clone_url']
        repo_counters['internal'] += 1
    else:
        repo_url = entry['clone_url']
        repo_counters['public'] += 1

    clone = f'git clone --mirror {repo_url}'
    repo_dir = f'{entry["name"]}.git'
    os.system(clone)

    if os.path.isdir(repo_dir):
        shutil.make_archive(entry['name'], format='zip', root_dir=pdata['target_dir'], base_dir=repo_dir)
        try:
            shutil.rmtree(repo_dir)
        except OSError as e:
            print("issues with " + repo_dir)
            repo_counters['error'] += 1
        else:
            s3_client = boto3.client("s3")
            s3_client.upload_file(f'{tasks["name"]}.zip',
                                  pdata['bucket_details']['target_bucket'],
                                  f'{pdata["bucket_details"]["bucket_key"]}/{tasks["name"].zip}')

        s3_client.put_object(
            Body=open(meta_file_name, 'rb'),
            Bucket=bucket_name,
            Key="{key}/{file_name}".format(key=bucket_key, file_name=meta_file_name),
        )

    os.remove(archive_name)
    os.remove(meta_file_name)


def main():
    max_pp = mp.cpu_count()
    asm_client = boto3.client('secretsmanager', region_name='eu-west-2')
    secret_values = json.loads(get_asm_parameter(asm_client=asm_client, name='service-backups/github/credentials'))
    root_dir = '/github-backup'
    process_data = {'bucket_details': {'target_bucket': 'tna-service-backup'}}
    repos_page = 100
    s3_client = boto3.client('s3')
    git_fetch = 'git fetch --all'

    Path(root_dir).mkdir(parents=True, exist_ok=True)
    os.chdir(root_dir)

    start_time = str(datetime.now())
    for repo in secret_values:
        bucket_suffix = str(datetime.now()).replace(' ', '_')
        process_data['bucket_details'][
            'bucket_key'] = f'github/{process_data["repo_login"]["organisation"]}_{bucket_suffix}'
        process_data['repo_login'] = {'user': repo['user'],
                                      'token': repo['token'],
                                      'organisation': repo['organisation']
                                      }
        repo_url = f'https://api.github.com/orgs/{process_data["repo_login"]["organisation"]}/repos'
        request_headers = {'Accept': 'application/vnd.github+json',
                           'X-GitHub-Api-Version': '2022-11-28',
                           f'Authorization': 'Bearer {process_data["repo_login"]["token"]}'
                           }
        }
        process_data['target_dir'] = '/github-backup'
        process_data['repos_per_page'] = 100
        current_page = 1
        while True:
            task_queue = Queue()
            done_queue = Queue()
            payload = {'per_page': repos_page, 'page': current_page}
            response = requests.get(repo_url, params=payload,
                                    headers=request_headers)
            response_json = response.json()
            if len(response_json) == 0:
                break

            for task in response_json:
                task_queue.put(task)

            for i in range(max_pp):
                Process(target=get_repos, args=(task_queue, done_queue, process_data)).start()

            for i in range(max_pp):
                task_queue.put('STOP')
            current_page += 1


if __name__ == '__main__':
    main()
