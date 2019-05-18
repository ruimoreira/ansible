#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: dms_replication_instance
short_description: creates or destroys a data migration replication instance
description:
    - creates or destroys a data migration replication instance,
      that carries out the actual work of replicating data.
version_added: "2.9"
options:
    state:
      description:
        - State of the endpoint
      default: present
      choices: ['present', 'absent']
    identifier:
        - Identifier for the instance
    allocatedstorage:
        description: 
          - The amount of storage (in gigabytes) to be initially 
            allocated for the replication instance
    instanceclass:
        description: 
          - The compute and memory capacity of the replication 
            instance as specified by the replication instance class.
        choices: ['dms.t2.micro', 'dms.t2.small','dms.t2.medium', 'dms.t2.large',
                 'dms.c4.large', 'dms.c4.xlarge','dms.c4.2xlarge', 'dms.c4.4xlarge'])
    vpcsecuritygroupids:
        description:
          - Specifies the VPC security group to be used with the replication instance. 
            The VPC security group must work with the VPC containing the replication instance.
    availabilityzone:
        description:
          - The EC2 Availability Zone that the replication instance will be created in.
    subnetgroupidentifier:
        description:
          -  A subnet group to associate with the replication instance.
    preferredmaintenancewindow:
        description:
          - The weekly time range during which system maintenance can occur, 
            in Universal Coordinated Time (UTC). Format: ddd:hh24:mi-ddd:hh24:mi
    multiaz:
        description:
          - Specifies if the replication instance is a Multi-AZ deployment.
            You cannot set the AvailabilityZone parameter if the Multi-AZ parameter is set to true.
    engineversion:
        description:
          - The engine version number of the replication instance.
    autominorversionupgrade:
        description:
          - Indicates that minor engine upgrades will be applied automatically 
          to the replication instance during the maintenance window.
        type: bool
        default: 'true'
    kmskeyid:
        description:
          - The AWS KMS key identifier that is used to encrypt the content on the replication instance. 
          If you don't specify a value for the KmsKeyId parameter, then AWS DMS uses your default encryption key
    publiclyaccessible:
        description:
          - Specifies the accessibility options for the replication instance. 
          A value of true represents an instance with a public IP address
    dnsnameservers:
        description:
          - A list of DNS name servers supported for the replication instance.
    '''

EXAMPLES = '''
'''

RETURN = ''' # '''
__metaclass__ = type
import traceback
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, HAS_BOTO3, \
    camel_dict_to_snake_dict, get_aws_connection_info, AWSRetry
try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

backoff_params = dict(tries=5, delay=1, backoff=1.5)
@AWSRetry.backoff(**backoff_params)
def describe_instance(connection, instance_identifier):
    """checks if instance exists"""
    try:
        instance_filter = dict(Name='replication-instance-id',
                               Values=[instance_identifier])
        return connection.describe_replication_instances(Filters=[instance_filter])
    except botocore.exceptions.ClientError:
        return {'ReplicationInstances': []}


def get_dms_client(aws_connect_params, client_region, ec2_url):
    client_params = dict(
        module=module,
        conn_type='client',
        resource='dms',
        region=client_region,
        endpoint=ec2_url,
        **aws_connect_params
    )
    return boto3_conn(**client_params)


def instance_exists(instance):
    """ Returns boolean based on the existance of the endpoint
    :param endpoint: dict containing the described endpoint
    :return: bool
    """
    return bool(len(instance['ReplicationInstances']))

def create_module_params():
    """
    Reads the module parameters and returns a dict
    :return: dict
    """
    instance_parameters = dict(
        ReplicationInstanceIdentifier = module.params.get('identifier'),
        AllocatedStorage = module.params.get('allocatedstorage'),
    )

    return instance_parameters

def main():
    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        identifier=dict(required=True),
        allocatedstorage=dict(type='int'),
        instanceclass=dict(required=True, choices=['dms.t2.micro', 'dms.t2.small',
                                                   'dms.t2.medium', 'dms.t2.large',
                                                   'dms.c4.large', 'dms.c4.xlarge',
                                                   'dms.c4.2xlarge', 'dms.c4.4xlarge']),
        vpcsecuritygroupids=dict(type='list'),
        availabilityzone=dict(),
        subnetgroupidentifier=dict(),
        preferredmaintenancewindow=dict(),
        multiaz=dict(type='bool', default=False),
        engineversion=dict(),
        autominorversionupgrade=dict(type='bool', default=True),
        kmskeyid=dict(),
        publiclyaccessible=dict(type='bool', default=True),
        dnsnameservers=dict(),
        tags=dict(type='list'),

    )
    global module
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[],
        supports_check_mode=False
    )
    exit_message = None
    changed = False
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')
    state = module.params.get('state')
    aws_config_region, ec2_url, aws_connect_params = \
        get_aws_connection_info(module, boto3=True)
    dmsclient = get_dms_client(aws_connect_params, aws_config_region, ec2_url)
    replication_instance = describe_instance(dmsclient,
                                             module.params.get('identifier'))
    if state == 'present':
        if instance_exists(replication_instance):
            module.exit_json(changed=changed, msg=argument_spec)
    module.exit_json(changed=changed, msg=exit_message)

if __name__ == '__main__':
    main()
