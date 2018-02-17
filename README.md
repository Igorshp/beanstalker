Elastic Beanstalk Configuration script
======================================

Allows easy configuration of environment variables for Beanstalk applications with version controlled files.

Tests
=====
TravisCI: [![Build Status](https://travis-ci.org/Igorshp/beanstalker.svg?branch=master)](https://travis-ci.org/Igorshp/beanstalker)

Usage:
=====


Generate yaml file from existing application enviornment
```
./beanstalker.py get <region> <app_name> <env_id>
```
print configuration in yaml format for existing environment
Simply save it to a file with a sensible name:

```
./beanstalker.py get <region> <app_name> <env_id> > <app-name>-<tag>.yml
```

The new config yml file can be commited to version control.
the structure is as follows:

```
ApplicationName: <app_name>
EnvironmentId: <env_id>
EnvironmentName: [name of environment] (not used for lookup, just for readability)
Region: <region>
EnvConfig:
    [list of env config variables]
```

Region, ApplicationName and EnvironmentId are used in environment lookup during update. 

To update the environment, edit any of the EnvConfig variables and run

```
./beanstalker.py update <configfile>.yml
```

The config in the file will be compared with current live application and user is presented with the diff (if any changes are detected)

```
The following options will be ADDED:
    NEW_OPTION: new val"
Following variables will be UPDATED:
    DEBUG: False-> True
    OPTION_ONE: some_val -> some_other_val 
The following options will be REMOVED:
    REDUNDANT_OPTION
    REDUNDANT_OPTION2

Update environment? [yes/no]:
```

Typing in 'yes' will attempt to update the environment. Restart will happen automaticaly


