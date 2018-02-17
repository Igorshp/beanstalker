from unittest import TestCase
from datetime import datetime
import beanstalker
import boto3
from botocore.stub import Stubber


class TestBeanstalker(TestCase):

    testDict1 = {
        "param1": "val1",
        "param2": "val2",
        "param3": "val3",
        "param4": "val4",
        "param5": "val5",
        "param6": "val6",
        "param7": "val7",
        "param8": "val8",
        "param9": "val9",
    }
    def get_stub_client(self):
        client = boto3.client('elasticbeanstalk')
        return client

    def test_create_env_option(self):
        NAME = 'testName'
        VALUE = 'testValue'
        option = beanstalker.create_env_option(NAME, VALUE)
        self.assertEqual(option['Namespace'], 'aws:elasticbeanstalk:application:environment')
        self.assertEqual(option['OptionName'], NAME)
        self.assertEqual(option['Value'], VALUE)

    def test_dict_compare_equals(self):
        added, removed, modified, same = beanstalker.dict_compare(self.testDict1, self.testDict1)
        self.assertFalse(added)
        self.assertFalse(removed)
        self.assertFalse(modified)
        self.assertEqual(len(self.testDict1), len(same))

    def test_dict_compare_added(self):
        existing = dict(self.testDict1)
        proposed = dict(self.testDict1)
        proposed['newparam'] = 'newval'
        added, removed, modified, same = beanstalker.dict_compare(proposed, existing)
        self.assertFalse(removed)
        self.assertFalse(modified)
        self.assertEqual(list(added)[0], 'newparam')
        self.assertEqual(len(same), len(existing))

    def test_dict_compare_removed(self):
        existing = dict(self.testDict1)
        proposed = dict(self.testDict1)
        del proposed['param4']
        added, removed, modified, same = beanstalker.dict_compare(proposed, existing)
        self.assertFalse(added)
        self.assertEqual(list(removed)[0], 'param4')
        self.assertFalse(modified)
        self.assertEqual(len(same), len(existing) - 1)

    def test_dict_compare_modified(self):
        existing = dict(self.testDict1)
        proposed = dict(self.testDict1)
        proposed['param2'] = 'newval'
        added, removed, modified, same = beanstalker.dict_compare(proposed, existing)
        self.assertFalse(added)
        self.assertFalse(removed)
        self.assertEquals(modified['param2'][0], 'newval')
        self.assertEqual(len(same), len(existing) - 1)

    def test_describe_environment(self):
        APP_NAME = 'testAppName'
        ENV_ID = 'testEnvID'
        client = beanstalker.get_client()
        response = {
            "Environments": [
                {"EnvironmentName": "testEnv"}
            ]
        }
        expected_params = {
            "ApplicationName":APP_NAME,
            "EnvironmentIds": [ENV_ID],
        }
        stubber = Stubber(client)
        stubber.add_response("describe_environments", response, expected_params)
        stubber.activate()
        env = beanstalker.describe_environment(client, APP_NAME, ENV_ID)
        self.assertEquals(env["EnvironmentName"], "testEnv")

    def test_get_environment_variables(self):
        client = beanstalker.get_client()
        APP_NAME = 'testAppName'
        ENV_NAME = 'testEnvName'
        client = beanstalker.get_client()
        response = {
            'ConfigurationSettings': [
                {
                    'SolutionStackName': 'string',
                    'PlatformArn': 'string',
                    'ApplicationName': 'string',
                    'TemplateName': 'string',
                    'Description': 'string',
                    'EnvironmentName': 'string',
                    'DeploymentStatus': 'pending',
                    'DateCreated': datetime(2015, 1, 1),
                    'DateUpdated': datetime(2015, 1, 1),
                    'OptionSettings': [
                        {
                            'ResourceName': 'string',
                            'Namespace': 'string',
                            'OptionName': 'other1',
                            'Value': 'otherval1'
                        },
                        {
                            'ResourceName': 'string',
                            'Namespace': 'aws:elasticbeanstalk:application:environment',
                            'OptionName': 'envoption1',
                            'Value': 'envval1'
                        },
                    ]
                },
            ]
        }
        expected_params = {
            "ApplicationName":APP_NAME,
            "EnvironmentName": ENV_NAME,
        }
        stubber = Stubber(client)
        stubber.add_response("describe_configuration_settings", response, expected_params)
        stubber.activate()
        env_config = beanstalker.get_environment_variables(client, expected_params)
        self.assertEqual(len(env_config), 1)
        self.assertEqual(env_config['envoption1'], 'envval1')
        print(env_config)











