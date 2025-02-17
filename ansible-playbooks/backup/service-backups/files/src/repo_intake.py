import requests
import json
import shutil
import boto3
import os
import tarfile
from pathlib import Path
from datetime import datetime, timedelta
from private_tools import get_asm_parameter, sha256sum, sha1sum

def main():
    asm_key = os.environ['ASM_KEY']
    access_point = os.environ['S3_ACCESS_POINT']
    root_dir = '/github-backup'
    zip_dir = '/github-zips'
    tar_dir = '/github-tar'
    ap_dir  = 'tna-external-services/github'

    # read repo credentials from ASM
    secret_values = json.loads(get_asm_parameter(name=asm_key))

    s3_client = boto3.client("s3")
    repos_per_page = 100
    git_fetch = "git fetch --all"

    Path(root_dir).mkdir(parents=True, exist_ok=True)
    Path(zip_dir).mkdir(parents=True, exist_ok=True)
    Path(tar_dir).mkdir(parents=True, exist_ok=True)

    start_time = str(datetime.now())
    for repo in secret_values:
        os.chdir(root_dir)
        current_page = 1
        private_repos = 0
        public_repos = 0

        url = f'https://api.github.com/orgs/{repo["organisation"]}/repos'
        headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
            'Authorization': f'Bearer {repo["token"]}'
        }

        while True:
            payload = {'per_page': repos_per_page, 'page': current_page}
            response = requests.get(url, params=payload, headers=headers)
            response_json = response.json()
            if len(response_json) == 0:
                break

            for entry in response_json:
                # clone github repo
                meta_file_name = f'{entry["name"]}.meta.json'
                archive_name = f'{entry["name"]}.zip'

                if entry["private"]:
                    url_parts = entry['clone_url'].split('//')
                    repo_url = f'{url_parts[0]}//{repo["user"]}:{repo["token"]}@{url_parts[1]}'
                    private_repos += 1
                else:
                    repo_url = entry['clone_url']
                    public_repos += 1

                clone = f'git clone --mirror {repo_url}'
                repo_dir = f'{entry["name"]}.git'
                os.system(clone)

                shutil.make_archive(entry['name'], format='zip', root_dir=root_dir, base_dir=repo_dir)
                shutil.move(f'{root_dir}/{archive_name}', zip_dir)
                shutil.rmtree(repo_dir)

            current_page += 1

        # create a tar file of the entire github organistion
        tar_name = f'{repo["organisation"]}_{str(datetime.now()).replace(" ", "_").replace(":", "-")}.tar'
        tar_file = f'{tar_dir}/{tar_name}'
        with tarfile.open(tar_file, 'w') as tar:
            for entry in os.scandir(zip_dir):
                if entry.is_file():
                    tar.add(f'{zip_dir}/{entry.name}')
                    os.remove(f'{zip_dir}/{entry.name}')

        s3_client.upload_file(tar_file, access_point, f'{ap_dir}/{tar_name}',
                              ExtraArgs={'Metadata': {'x-amz-meta-legal_hold': 'ON',
                                                      'x-amz-meta-lock_mode': 'governance',
                                                      'x-amz-meta-retain_until_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
                                                      }
                                         }
                              )
        os.remove(tar_file)

if __name__ == "__main__":
    main()
