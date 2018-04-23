import boto3
import collections
import datetime
import sys
import hashlib
import random
import time

ec2 = boto3.client ( 'ec2' )
asg = boto3.client ( 'autoscaling' )


def lambda_handler(event , context):
    # TODO implement
    # Variable inst will be populated with all the instances having name given to = Values.
    inst = ec2.describe_instances (
        Filters=[
            {'Name': 'tag:Name' , 'Values': ['prdsrv']} ,
        ]
    ).get (
        'Reservations' , []
    )

    instances = sum (
        [
            [i for i in r['Instances']]
            for r in inst
        ] , [] )

    for instance in instances:
        create_time = datetime.datetime.now ()
        # This variable is used to add date time on AMI description
        create_fmt = create_time.strftime ( '%Y-%m-%d' )
        # Random code generated in order to assign a name to AMI. This is important otherwise automation will fail
        randCode = hashlib.sha256 ( str ( random.getrandbits ( 256 ) ).encode ( 'utf-8' ) ).hexdigest ()
        # AMi is being created at this line
        AMIid = ec2.create_image ( InstanceId=instance['InstanceId'] , Name=randCode[:25] ,
                                   Description="Auto generated AMI of " + instance[
                                       'InstanceId'] + " created on " + create_fmt , NoReboot=True , DryRun=False )
        # This section is responsible for adding Tags to AMI. Go ahead add your own Tags. Stack variable holds the Your Cloudformation tag name.
        Stack = "xx"
        ec2.create_tags (
            Resources=[AMIid['ImageId']] ,
            Tags=[
                {'Key': 'Name' , 'Value': 'MyPrdServre'} ,
                {'Key': 'Date' , 'Value': datetime.datetime.now ().strftime ( "%Y-%m-%d" )} ,
                {'Key': 'Time' , 'Value': datetime.datetime.now ().strftime ( "%H:%M" )} ,
                {'Key': 'Stack' , 'Value': Stack} ,
            ]
        )
        # End of addtion Tags

    # This variable holds auto generated hex code, which will be used for Launch Config name.
    lc_name = hashlib.sha256 ( str ( random.getrandbits ( 256 ) ).encode ( 'utf-8' ) ).hexdigest ()
    # Creating Launch Configurations
    response = asg.create_launch_configuration ( LaunchConfigurationName=lc_name ,
                                                 ImageId=AMIid['ImageId'] ,
                                                 KeyName='xyz' ,
                                                 SecurityGroups=['sg-123456' , ] ,
                                                 IamInstanceProfile='RL_invoke_lambda_function' ,
                                                 InstanceType='t2.nano' )
    # Updating Auto Scalling Group. Remember you need to put actual ASG name on AutoScalingGroupName
    # You need to add all your ASG properties here before use. This a must step.
    response = asg.update_auto_scaling_group (
        AutoScalingGroupName='xx-prdserver-12345678' ,
        LaunchConfigurationName=lc_name ,
        MinSize=1 ,
        MaxSize=1 ,
        DesiredCapacity=1 ,
        AvailabilityZones=['ap-south-1b'] ,
        HealthCheckType='EC2' ,
        HealthCheckGracePeriod=900 ,
        VPCZoneIdentifier='subnet-12345678' ,
        TerminationPolicies=['Default'] ,
        NewInstancesProtectedFromScaleIn=False
    )
