#!/usr/bin/env python
import boto3
from botocore.exceptions import ClientError
import yaml
import pprint
import json
import argparse
import os
from os.path import basename, splitext

pp = pprint.PrettyPrinter(indent=4)
DEBUG = False

#TODO: add support for encryption of sensitive values
#TODO: add support for removing options
#TODO: add verification action such as 'plan' or 'verify'
#TODO: reorder yaml output so environment name and id are above EnvConfig

class EnvironmentNotFound(Exception):
    pass


def debug(msg):
    if DEBUG:
        print(msg)


def get_client(region="us-east-1"):
    return boto3.client('elasticbeanstalk', region_name=region)


def create_env_option(name: str, value: str) -> dict:
    return {
        'Namespace': 'aws:elasticbeanstalk:application:environment',
        'OptionName': name,
        'Value': str(value)
    }


def dict_compare(d1: dict, d2: dict):
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    added = d1_keys - d2_keys
    removed = d2_keys - d1_keys
    modified = {o: (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
    same = set(o for o in intersect_keys if d1[o] == d2[o])
    return added, removed, modified, same


def to_file(filename: str, content: str):
    with open(filename, 'w') as f:
        f.write(content)


def save_yaml(filename: str, data: dict) -> None:
    with open(filename, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)


def load_yaml(filename: str):
    with open(filename, 'r') as stream:
        # try:
        return yaml.load(stream)
        # except yaml.YAMLError as exc:
        #     print(exc)


def get_environment_variables(client, env: dict) -> dict:
    response = client.describe_configuration_settings(
        ApplicationName=env['ApplicationName'],
        EnvironmentName=env['EnvironmentName'],
    )
    applications = response['ConfigurationSettings']
    if len(applications) != 1:
        raise Exception("Multiple applications returned")
    application = applications[0]
    option_settings = application['OptionSettings']
    env_vars = {}
    for option in option_settings:
        if option['Namespace'] == 'aws:elasticbeanstalk:application:environment':
            env_vars[option['OptionName']] = option['Value']
    return env_vars

def get_applications(client) -> dict:
    apps = client.describe_applications()

    app_names = [ app['ApplicationName'] for app in apps['Applications']]
    return app_names

def get_environments(client, app_name) -> list:
    envs = client.describe_environments(ApplicationName=app_name)
    return envs['Environments']
     
    




def describe_environment(client, app_name: str, env_id: str) -> dict:
    response = client.describe_environments(
        ApplicationName=app_name,
        EnvironmentIds=[env_id]
    )
    if len(response['Environments']) != 1:
        raise EnvironmentNotFound()
    return response['Environments'][0]


def get_config(client, region, app_name, env_id) -> dict:
    get_applications(client)
    env = describe_environment(client, app_name, env_id)
    debug("getting config for app {}, env {} ({})".format(app_name, env['EnvironmentName'], env_id))
    env_vars = get_environment_variables(client, env)
    config = {
        "ApplicationName": app_name,
        "Region": region,
        "EnvironmentID": env_id,
        "EnvironmentName": env['EnvironmentName'],
        "EnvConfig": env_vars
    }
    return config
    # print(yaml.dump(config, default_flow_style=False))


def action_get(region: str, app_name: str, env_id: str, out_file: str):
    client = get_client(region)
    if not app_name:
        availiable_apps = get_applications(client)
        if len(availiable_apps) == 0:
            print("{} region doesn't have any beanstalk applications".format(region))
            return
        print("Availiable apps in {} region:".format(region))
        for idx, name in enumerate(availiable_apps):
            print("{}: {}".format(idx, name))
        item = input("Select application [0-{}] ".format(len(availiable_apps)-1))
        try:
            app_name = availiable_apps[int(item)]
        except (IndexError, ValueError):
            print("{} is invalid option. Quitting")
            return
        print("Selected {}".format(availiable_apps[int(item)]))
    if not env_id:
        print("env id not selected")
        availiable_envs = get_environments(client, app_name)
        if len(availiable_envs) == 0:
            print("{} doesn't have any environments".format(app_name))
            return
        print("Availiable environments for {}:".format(app_name))
        for idx, env in enumerate(availiable_envs):
            print("{}: {} ({})".format(idx, env['EnvironmentName'], env['EnvironmentId']))
        item = input("Select environment to pull config for [0-{}] ".format(len(availiable_envs)-1))
        try:
            env = availiable_envs[int(item)]
        except (IndexError, ValueError):
            print("{} is invalid option. Quitting")
            return
        print("Selected {}".format(env['EnvironmentName']))
        env_id = env['EnvironmentId']
    config = get_config(client, region, app_name, env_id)
    raw_yaml = yaml.dump(config, default_flow_style=False)
    print(raw_yaml)
    if not out_file:
        out_file = input("Enter output filename to save config to: ")
    out_file_base = basename(out_file)
    ext = splitext(out_file_base)[1]
    if not ext:
        out_file = out_file + ".yml"
    to_file(out_file, raw_yaml)
    print("Saved config to {}".format(out_file))
        


def update_env(client, app_name: str, env_id:str , options_to_update: dict, options_to_remove):
    option_settings = [create_env_option(k, v) for k, v in options_to_update.items()]
    # TODO: do the OptionsToRemove bit
    # remove_settings = [create_env_option(k, v) for k, v in options_to_remove.items()]
    # Handle whitespaces in names. cloudformation allows creation of variable names
    #with whitespaces at start / end, but everywhere else trims them.
    # possibly trim whitespaces from variable names and 'deduplicate' these from ToRemove set
    try:
        response = client.update_environment(
            ApplicationName=app_name,
            EnvironmentId=env_id,
            OptionSettings=option_settings,
            # OptionsToRemove=[
            #     {
            #         'ResourceName': 'string',
            #         'Namespace': 'string',
            #         'OptionName': 'string'
            #     },
            # ]
        )
    except ClientError as e:
        print("Client Error: {}".format(str(e)))
        print()
        print("NO CHANGES MADE. Please run the script again when environment state changes")
        return
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("Update SUCCESSFUL. Application '{}' environment '{}' is restarting".format(app_name,
                                                                                          response['EnvironmentName']))


def action_update(args: dict):
    file_config = load_yaml(args.file)
    # print(file_config.keys())
    proposed_config = file_config['EnvConfig']
    existing_config = get_config(file_config['Region'], file_config['ApplicationName'], file_config['EnvironmentID'])['EnvConfig']

    added, removed, modified, same = dict_compare(proposed_config, existing_config)

    update_required = False
    options_to_update = {}
    options_to_remove = {}
    if added:
        update_required = True
        print("Following variables will be ADDED:")
        for key in added:
            print("\t{}: {}".format(key, proposed_config[key]))
            options_to_update[key] = proposed_config[key]
    if removed:
        update_required = True
        print("Removed:")
        pp.pprint(removed)
    if modified:
        update_required = True
        print("Following variables will be UPDATED:")
        for key, (new, old) in modified.items():
            options_to_update[key] = new
            print("\t{}: {} -> {}".format(key, old, new))

    if update_required:
        if input("Update environment? [yes/no]: ") == 'yes':
            update_env(get_client(file_config['Region']), file_config['ApplicationName'], file_config['EnvironmentID'], options_to_update,
                       options_to_remove)
        else:
            print("Canceling operation")
    else:
        print("No changes found, environment is up to date")




def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('action', choices=["get", "update"])
    parser.add_argument('file', nargs='?')
    parser.add_argument('--app-name')
    parser.add_argument('--env-id')
    parser.add_argument('--region')
    parser.add_argument('--out-file')
    args = parser.parse_args()

    if args.action == 'get':
        action_get(args.region, args.app_name, args.env_id, args.out_file)
    elif args.action == 'update':
        action_update(args)
    else:
        print("unknown action")
        
        os.exit(1)

if __name__ == "__main__":
    main()
