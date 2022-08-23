import math
import subprocess
import time

import boto3

from ec2 import EC2
from logger import Logger
from utils import parse_arguments, get_size
from volume import Volume

if __name__ == '__main__':
    args = parse_arguments()

    logger = Logger(
        verbose=args.verbose
    )

    size = get_size(args.path)

    session = boto3.Session()
    client = boto3.client('ec2')
    resource = boto3.resource('ec2')

    # 1. Create an EC2 instance and wait for it to be 'Ready'
    ec2 = EC2(client, resource, args.keyname, logger)
    ec2.create_instance()
    ec2.wait_for_instance()

    # This takes a lot of time but is necessary since even
    # after the instance is in the 'Running' state,
    # sometimes the instance isn't ready to accept traffic
    # which causes the transfer to fail
    ec2.wait_for_checks()

    # 2. Create an EBS volume of twice the size of our data
    #    and attach it to our EC2 instance
    volume = Volume(
        session,
        client,
        resource,
        ec2.get_availability_zone(),
        math.ceil((size * 2) / 1000 / 1000 / 1000),
        logger
    )
    volume.create()
    volume.attach_to_ec2_instance(ec2.instance_id)

    # This is again necessary here since even after attaching
    # our volume and it being in the 'Volume Attached' state,
    # sometimes it takes the instance some time to configure
    # the device. Otherwise, sometimes the writing fails with
    # the error 'dd: /dev/xbd1 Device not configured'
    time.sleep(60)

    # 3. tar(1) the files/directories to back up
    tarCommand = 'tar -c -f - {}'.format(args.path)
    tarProcess = subprocess.Popen(
        tarCommand.split(' '),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    # 4. Pipe the output of tar(1) to dd on the remote machine
    #    which will write the data to our EBS volume
    ddCommand = 'ssh -o StrictHostKeyChecking=no -i ~/.ssh/{}.pem root@{} dd of=/dev/xbd1'.format(
        args.keyname, ec2.get_public_dns()
    )
    ddProcess = subprocess.Popen(
        ddCommand.split(' '),
        stdin=tarProcess.stdout,
        stderr=subprocess.DEVNULL
    )
    ddProcess.wait()

    # 5. Our backup is now complete, so detach the EBS volume
    #    from the EC2 instance
    volume.detach_from_ec2_instance(ec2.instance_id)

    # 6. Terminate the EC2 instance we created for attaching
    #    the EBS volume
    ec2.terminate_instance()

    # 7. Finally, write the id of the EBS volume we used to
    #    store our backup to STDOUT and exit
    print(volume.volume_id)
    exit(0)
