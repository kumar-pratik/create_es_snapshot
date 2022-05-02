### Elastic Backup Configuration

The script configures the s3 buckets and
then initiates snapshot process. The elasticsearch
should have "cloud-aws" plugin installed. 

##### _Requirements_
we need the following python packages:
  - Jinja2==2.11.3
  - PyYaml==5.4.1
  - requests==2.25.1

We will also require python3 installed 
and pip version 21.0.1

##### Using `venv` 
Python3 comes with virtual env module which
can help keep the env isolated from root
packages.

*Steps*:
  - within the folder use the following
command:
    ```
    python3 -m venv .
    ```
  - this will setup a venv folder and then we
need to activate the virtual env:
    ```
    source venv/bin/activate
    ```
  - Once activated the pip can be upgraded easily.
  - now, we can install the packages
and they won't be affecting our root system.
    
##### Running the Script
The `configuration` folder contains
the templates and yamls.

The YAML files are used as meta data and 
contains the configuration that we will use.

The templates will help generate the payload
for every curl request.

we have the following structure of the yaml
```
---
config:
  url: "<URL for the elasticsearch instance>"
  repository: "<name of repository>"
  # could be anything that makes sense.
  ## !! Please do not use invalid chars.
  bucket:
    s3: "<name of s3 bucket>"
    # the bucket where we want to store the backup.
    #!! it will auto create a bucket if not present.
    #!! please be careful with creds and rotate them.
    region: "us-east-1"
    # not required field.
    snapshot:
      indices:
        - <index-*>
        - <_all>
        # use index names or individual
        # patterns. to keep back up of all 
        # indices is `_all`. refer to Index Patterns
```

Run the script as follows:
````
 #1 verify your yamls
 # verify your snapshot
 # for example :
 # hit this url to check for the progress.
 # http://localhost:9210/_snapshot/<config.repository>/<config.bucket.snapshot.name>?pretty
 # refer to your yamls for the respective cluster for repository and bucket name. 
 # export the aws access key and secret key
 
 export AWS_ACCESS_KEY_ID=**********
 export AWS_SECRET_ACCESS_KEY=***********
 
 ./elastic_snapshot.py --metadata configuruation/es.yaml
````