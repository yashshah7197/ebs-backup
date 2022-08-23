class Volume:
    def __init__(self, session, client, resource, availability_zone, size, logger):
        self.session = session
        self.resource = resource
        self.client = client
        self.availability_zone = availability_zone
        self.size = size
        self.volume_id = None
        self.device_name = '/dev/sdf'
        self.logger = logger

    def create(self):
        self.logger.log('Creating an EBS volume...')

        response = self.client.create_volume(
            AvailabilityZone=self.availability_zone,
            Size=self.size
        )
        self.volume_id = response['VolumeId']

        self.logger.log('Successfully created an EBS volume!')

    def attach_to_ec2_instance(self, instance_id):
        self.logger.log('Attaching the EBS volume to the instance...')

        waiter = self.client.get_waiter('volume_available')
        waiter.wait(
            VolumeIds=[self.volume_id],
            DryRun=False
        )

        volume = self.resource.Volume(self.volume_id)
        volume.attach_to_instance(
            Device=self.device_name,
            InstanceId=instance_id
        )

        waiter = self.client.get_waiter('volume_in_use')
        waiter.wait(
            VolumeIds=[self.volume_id],
            DryRun=False
        )

        self.logger.log('Successfully attached the EBS volume to the instance!')

    def detach_from_ec2_instance(self, instance_id):
        self.logger.log('Detaching the EBS volume from the instance...')

        volume = self.resource.Volume(self.volume_id)
        volume.detach_from_instance(
            Device=self.device_name,
            InstanceId=instance_id
        )

        waiter = self.client.get_waiter('volume_available')
        waiter.wait(
            VolumeIds=[self.volume_id],
            DryRun=False
        )

        self.logger.log('Successfully detached the EBS volume from the instance!')
