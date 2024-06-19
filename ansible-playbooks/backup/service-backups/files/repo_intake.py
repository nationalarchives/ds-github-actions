import requests
import json
import subprocess
import shutil
import boto3
import os
import hashlib
from pathlib import Path
from datetime import datetime


def get_asm_parameter(asm_client, name: str) -> json:
    secrets = asm_client.get_secret_value(SecretId=name)
    return secrets["SecretString"]


def sha256sum(filename: str) -> str:
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()


def sha1sum(filename: str) -> str:
    h = hashlib.sha1()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()


def rmdir(directory: str) -> None:
    directory = Path(directory)
    for item in directory.iterdir():
        if item.is_dir():
            directory.rmdir(item)
        else:
            item.unlink()
    directory.rmdir()


def s3_folder_exists(s3_client, bucket: str, path: str) -> bool:
    path = path.rstrip('/')
    resp = s3_client.list_objects(Bucket=bucket, Prefix=path, Delimiter='/', MaxKeys=1)
    return 'CommonPrefixes' in resp


def main():
    bucket_name = "tna-service-backup"
    bucket_base_key = "github"
    bucket_index = str(datetime.now()).replace(" ", "_")
    root_dir = "/github-backup"

    # read repo credentials from ASM
    asm_client = boto3.client("secretsmanager", region_name="eu-west-2")
    secret_values = json.loads(get_asm_parameter(asm_client=asm_client, name="service-backups/github/credentials"))

    s3_client = boto3.client("s3")
    repos_per_page = 100
    git_fetch = "git fetch --all"

    Path(root_dir).mkdir(parents=True, exist_ok=True)
    os.chdir(root_dir)

    start_time = str(datetime.now())
    for repo in secret_values:
        user = repo["user"]
        token = repo["token"]
        organisation = repo["organisation"]
        current_page = 1
        private_repos = 0
        public_repos = 0
        bucket_key = "{base}/{org}_{index}".format(base=bucket_base_key, org=organisation, index=bucket_index)

        url = "https://api.github.com/orgs/{org}/repos".format(org=organisation)
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "Bearer {key}".format(key=token)
        }

        while True:
            payload = {"per_page": repos_per_page, "page": current_page}
            response = requests.get(url, params=payload, headers=headers)
            response_json = response.json()
            if len(response_json) == 0:
                break

            for entry in response_json:
                # clone github repo
                meta_file_name = "{repo_name}.meta.json".format(repo_name=entry["name"])
                archive_name = "{name}.zip".format(name=entry["name"])

                if entry["private"]:
                    url_parts = entry["clone_url"].split("//")
                    github_creds = "{user}:{token}@".format(user=user,token=token)
                    repo_url = url_parts[0] + "//" + github_creds + url_parts[1]
                    private_repos +=1
                else:
                    repo_url = entry["clone_url"]
                    public_repos +=1

                clone = "git clone {repo}".format(repo=repo_url)
                os.system(clone)
                os.chdir(entry["name"])
                git_fetch = "git fetch --all"
                os.system(git_fetch)
                os.chdir("..")

                shutil.make_archive(entry["name"], format='zip', root_dir=root_dir, base_dir=entry["name"])

                try:
                    shutil.rmtree(entry["name"])
                except OSError as e:
                    print("issues with " + entry["name"])

                # run checksum
                meta_file = open(meta_file_name, "a")
                meta_file.write('{\n')
                meta_file.write('  "file_name":"{name}",\n'.format(name=entry["name"]))
                meta_file.write('  "file_size":"{size}",\n'.format(size=str(os.path.getsize(archive_name))))
                meta_file.write('  "created_at:":"{date}",\n'.format(date=str(os.path.getctime(archive_name))))
                meta_file.write('  "sha1":"{sha1}",\n'.format(sha1=sha1sum(archive_name)))
                meta_file.write('  "sha256":"{sha256}",\n'.format(sha256=sha256sum(archive_name)))
                meta_file.write('}\n')
                meta_file.close()

                s3_client.put_object(
                    Body=open(archive_name, 'rb'),
                    Bucket=bucket_name,
                    Key="{key}/{file_name}".format(key=bucket_key, file_name=archive_name),
                )

                s3_client.put_object(
                    Body=open(meta_file_name, 'rb'),
                    Bucket=bucket_name,
                    Key="{key}/{file_name}".format(key=bucket_key, file_name=meta_file_name),
                )

                os.remove(archive_name)
                os.remove(meta_file_name)

            current_page += 1

        summary_file_name = "_backup-summary.log"

        summary_file = open(summary_file_name, "a")
        summary_file.write("organisation: {org}\n".format(org=organisation))
        summary_file.write("start at: {time}\n".format(time=start_time))
        summary_file.write("end at: {count}\n".format(count=str(datetime.now())))
        summary_file.write("private repos: {count}\n".format(count=str(private_repos)))
        summary_file.write("public repos: {count}\n".format(count=str(public_repos)))
        summary_file.write("total repos:  {count}\n".format(count=str(private_repos + public_repos)))
        summary_file.close()

        s3_client.put_object(
            Body=open(summary_file_name, 'rb'),
            Bucket=bucket_name,
            Key="{key}/{file_name}".format(key=bucket_key, file_name=summary_file_name),
        )
        os.remove(summary_file_name)


if __name__ == "__main__":
    main()
