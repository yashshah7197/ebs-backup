class EC2:
    def __init__(self, client, resource, keyname, logger):
        self.resource = resource
        self.client = client
        self.image_id = 'ami-0018b2d98332ba7e3'
        self.instance_type = 't2.micro'
        self.instance_id = None
        self.keyname = keyname
        self.logger = logger

    def should_create_security_group(self):
        try:
            self.client.describe_security_groups(GroupNames=['ebs-backup'])
            return False
        except:
            return True

    def create_security_group(self):
        self.logger.log('Creating and configuring a security group...')

        try:
            self.resource.create_security_group(
                GroupName='ebs-backup',
                Description='Security group for ebs-backup'
            )

            self.client.authorize_security_group_ingress(
                GroupName='ebs-backup',
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )

            self.logger.log('Security group created and configured successfully!')
        except:
            self.logger.log('Failed to create and configure a security group!')
            raise

    def create_instance(self):
        if self.should_create_security_group():
            self.create_security_group()

        self.logger.log('Creating an EC2 instance...')

        try:
            response = self.resource.create_instances(
                ImageId=self.image_id,
                InstanceType=self.instance_type,
                MinCount=1,
                MaxCount=1,
                SecurityGroups=['ebs-backup'],
                KeyName=self.keyname
            )

            self.instance_id = response[0].id

            self.logger.log('Successfully created EC2 instance {}!'.format(self.instance_id))
        except:
            self.logger.log('Failed to create EC2 instance!')
            raise

    def wait_for_instance(self):
        self.logger.log("Waiting for instance to be in 'Running' state...")

        waiter = self.client.get_waiter('instance_running')
        waiter.wait(
            InstanceIds=[self.instance_id],
            DryRun=False
        )

        self.logger.log("Instance is now in 'Running' state!")

    def wait_for_checks(self):
        self.logger.log('Waiting for health checks to pass...')

        waiter = self.client.get_waiter('system_status_ok')
        waiter.wait(
            InstanceIds=[self.instance_id],
            DryRun=False
        )

        waiter = self.client.get_waiter('instance_status_ok')
        waiter.wait(
            InstanceIds=[self.instance_id],
            DryRun=False
        )

        self.logger.log('Successfully passed health checks!')

    def terminate_instance(self):
        self.logger.log('Terminating instance...')

        self.resource.instances.filter(InstanceIds=[self.instance_id]).terminate()

        waiter = self.client.get_waiter('instance_terminated')
        waiter.wait(
            InstanceIds=[self.instance_id],
            DryRun=False
        )

        self.logger.log('Successfully terminated instance!')

    def get_availability_zone(self):
        instance = list(self.resource.instances.filter(InstanceIds=[self.instance_id]))[0]
        return instance.network_interfaces[0].subnet.availability_zone

    def get_public_dns(self):
        instance = list(self.resource.instances.filter(InstanceIds=[self.instance_id]))[0]
        return instance.public_dns_name
