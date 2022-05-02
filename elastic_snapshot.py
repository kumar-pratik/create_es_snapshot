#!/usr/bin/env python3

from string import Template
from yaml import load, YAMLLoadWarning, SafeLoader
from jinja2 import (Environment, FileSystemLoader,
                    TemplateError)
from os import getcwd, environ
from os.path import isfile
from requests import put, post, get, RequestException
from json import loads, JSONDecodeError
from argparse import ArgumentParser
from datetime import date

EXCEPTION_MSG = Template("$className: $message")


def substitute_placeholder(exception_obj):
    """
    prints exception template by substituting params.
    :param exception_obj: An Exception Object
    :return: a string which has the message.
    """
    return EXCEPTION_MSG.safe_substitute(
        className=exception_obj.__class__.__name__,
        message=exception_obj
    )


def repository_create(repository):
    """
    creates URI to follow after ES url
    :param repository: name of the repository.
    :return: string uri to use after ES Url.
    """
    uri = f"/_snapshot/{repository}"
    return uri


def snapshot_verify(repository):
    """
    creates URI to follow after ES url.
    :param repository: repository name which we configured.
    :return: a string uri to append after ES url.
    """
    uri = f"/_snapshot/{repository}/_verify?pretty"
    return uri


def snapshot_create(repository, snapshot):
    """
    creates URI to request snapshot creation.
    :param repository: name of the repository.
    :param snapshot: name to give to the snapshot.
    :return: a string uri to append after ES url.
    """
    uri = f"/_snapshot/{repository}/{snapshot}?pretty"
    return uri


def read_configuration(location):
    """
    parses the yaml doc given by a location.
    :param location: a path (relative/absolute)
    :return: A json decoded python Object.
    """
    try:
        with open(location, 'r') as conf:
            return load(conf, Loader=SafeLoader)
    except FileNotFoundError as fe:
        print(substitute_placeholder(fe))
        return None
    except YAMLLoadWarning as fe:
        print(substitute_placeholder(fe))
        return None


def generate_payload(template_location, metadata, outfile):
    """
    reads the jinja template and fills with meta data.
    the output is saved to a file given by the location
    in outfile.
    Creates the out_file if it doesn't exist.
    :param template_location: a path to the jinja template.
    relative path only.
    :param metadata: an already loaded json object.
    :param outfile: path to save the file on.
    :return: Numbers to bytes written (if successful)
    else, it will send None
    """
    try:
        if metadata is not None:
            loader = FileSystemLoader(getcwd())
            env = Environment(loader=loader)
            template = env.get_template(template_location)
            with open(outfile, 'w+') as payload:
                print(metadata)
                content = template.render(metadata)
                return payload.write(content)
        else:
            print("metadata is empty.")
            return None
    except IOError as fe:
        print(substitute_placeholder(fe))
        return None
    except TemplateError as fe:
        print(substitute_placeholder(fe))
        return None
    except ValueError as fe:
        print(substitute_placeholder(fe))
        return None


def check_if_reachable(es_url):
    """
    checks if the url is reachable.
    :param es_url: the url to contact ES.
    :return: boolean ; True in case of reachable.
    """
    return get(es_url).ok


def configure_repository(payload_location, es_url, repository_name):
    """
    configures the bucket to elasticsearch.
    :param payload_location: location of json
    template of the payload.
    :param es_url: url to connect to the ES.
    :return: returns the status code.
    """
    if check_if_reachable(es_url=es_url) \
            and isfile(payload_location):
        try:
            uri = repository_create(repository=repository_name)
            with open(payload_location, 'r') as payload:
                json_payload = load(payload, Loader=SafeLoader)
                return put(url=es_url + uri,
                           json=json_payload).status_code
        except FileNotFoundError as fe:
            print(substitute_placeholder(fe))
            return 404
        except JSONDecodeError as fe:
            print(substitute_placeholder(fe))
            return 406  # not acceptable.
        except Exception as fe:
            print(substitute_placeholder(fe))
            return 404
    else:
        return 404


def verify_bucket_configuration(es_url, repository):
    """
    verifies whether the bucket is configured.
    :param es_url: url to connect to ES.
    :param repository: name of repository to confirm.
    :return: returns response.
    """
    if check_if_reachable(es_url=es_url):
        try:
            uri = snapshot_verify(repository)
            response = loads(post(es_url + uri).content)
            return response
        except RequestException as fe:
            print(substitute_placeholder(fe))
            return None
        except JSONDecodeError as fe:
            print(substitute_placeholder(fe))
            return None


def create_snapshot(es_url, repository, snapshot, payload_location):
    """
    creates snapshot for the elasticsearch backup.
    :param es_url: url to es.
    :param repository: name of repository through
    which we will initiate the backup.
    :param snapshot: name of the snapshot.
    :param payload_location: request payload which will be
    used to confirm indices.
    :return: the response after request is thrown.
    """
    if check_if_reachable(es_url=es_url) and \
            isfile(payload_location):
        try:
            uri = snapshot_create(repository, snapshot)
            with open(payload_location, 'r') as payload:
                json_payload = load(payload, Loader=SafeLoader)
                response = loads(put(url=es_url + uri,
                                 json=json_payload).content)
                return response
        except RequestException as fe:
            print(substitute_placeholder(fe))
            return None
        except JSONDecodeError as fe:
            print(substitute_placeholder(fe))
            return None

def fill_template(template, metadata, outfile):
    if metadata is not None:
        written = generate_payload(template_location=template,
                                   metadata=metadata,
                                   outfile=outfile)
        if written == 0 or written is None:
            print("please check the metadata, it is must be none.")
    else:
        print("meta data didn't load; please check yamls")
        exit(1)


def entrypoint(bucket_template, snapshot_template, metadata):
    meta_values = read_configuration(metadata)
    bucket_payload = "configuration/bucket.json"
    snapshot_payload = "configuration/snapshot.json"
    es_url = meta_values["config"]["url"]
    repository = meta_values["config"]["repository"]
    today = date.today()
    snapshot_name = "snapshot-" + str(today)
    print(snapshot_name)
    meta_values['config']['bucket']['access_key'] = environ['AWS_ACCESS_KEY_ID']
    meta_values['config']['bucket']['access_secret'] = environ['AWS_SECRET_ACCESS_KEY']
    meta_values['config']['bucket']['snapshot']['name'] = snapshot_name
    print(es_url)
    fill_template(template=bucket_template,
                  metadata=meta_values,
                  outfile=bucket_payload)
    fill_template(template=snapshot_template,
                  metadata=meta_values,
                  outfile=snapshot_payload)
    print(configure_repository(es_url=es_url, repository_name=repository,
                               payload_location=bucket_payload))
    print(verify_bucket_configuration(es_url=es_url,
                                      repository=repository))
    print(create_snapshot(es_url=es_url,
                          repository=repository,
                          snapshot=snapshot_name,
                          payload_location=snapshot_payload))


def read_arguments(argv=None):
    arg_parser = ArgumentParser(
        description="Elastic Snapshot Engine")
    arg_parser.add_argument("--metadata",
                            help="yaml file location",
                            type=str,
                            default=None)
    return arg_parser.parse_args()

if __name__ == '__main__':
    bucket_template = "configuration/elastic_bucket.j2"
    snapshot_template = "configuration/elastic_snapshot.j2"
    args = read_arguments()
    metadata = args.metadata
    entrypoint(bucket_template=bucket_template,
               snapshot_template=snapshot_template,
               metadata=metadata)
