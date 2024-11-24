import boto3
import sys
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# AWS 클라이언트 초기화
ec2 = boto3.client('ec2', region_name='ap-northeast-2')

def list_instances():
    """EC2 인스턴스 목록 조회"""
    print("Listing instances...")
    try:
        instances = ec2.describe_instances()
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                print(f"[id] {instance['InstanceId']}, "
                      f"[AMI] {instance['ImageId']}, "
                      f"[type] {instance['InstanceType']}, "
                      f"[state] {instance['State']['Name']}, "
                      f"[public IP] {instance.get('PublicIpAddress', 'N/A')}, "
                      f"[launch time] {instance['LaunchTime']}, "
                      f"[monitoring state] {instance['Monitoring']['State']}")
    except Exception as e:
        print(f"Error listing instances: {e}")

def available_zones():
    """사용 가능한 가용 영역 조회"""
    print("Available zones...")
    try:
        zones = ec2.describe_availability_zones()
        for zone in zones['AvailabilityZones']:
            print(f"[id] {zone['ZoneId']}, [region] {zone['RegionName']}, [zone] {zone['ZoneName']}")
        print(f"You have access to {len(zones['AvailabilityZones'])} Availability Zones.")
    except Exception as e:
        print(f"Error retrieving availability zones: {e}")

def start_instance(instance_id):
    """인스턴스 시작"""
    print(f"Starting instance {instance_id}...")
    try:
        response = ec2.start_instances(InstanceIds=[instance_id])
        for instance in response['StartingInstances']:
            print(f"Instance {instance['InstanceId']} is now {instance['CurrentState']['Name']}.")
    except Exception as e:
        print(f"Error starting instance: {e}")

def stop_instance(instance_id):
    """인스턴스 중지"""
    print(f"Stopping instance {instance_id}...")
    try:
        response = ec2.stop_instances(InstanceIds=[instance_id])
        for instance in response['StoppingInstances']:
            print(f"Instance {instance['InstanceId']} is now {instance['CurrentState']['Name']}.")
    except Exception as e:
        print(f"Error stopping instance: {e}")

def reboot_instance(instance_id):
    """인스턴스 재부팅"""
    print(f"Rebooting instance {instance_id}...")
    try:
        ec2.reboot_instances(InstanceIds=[instance_id])
        print(f"Successfully rebooted instance {instance_id}.")
    except Exception as e:
        print(f"Error rebooting instance: {e}")

def create_instance(ami_id, instance_type='t2.micro', key_name=None, security_group=None):
    """새 인스턴스 생성"""
    print(f"Creating instance with AMI {ami_id}...")
    try:
        response = ec2.run_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            MinCount=1,
            MaxCount=1,
            KeyName=key_name,
            SecurityGroupIds=[security_group] if security_group else None
        )
        instance_id = response['Instances'][0]['InstanceId']
        print(f"Successfully started EC2 instance {instance_id} based on AMI {ami_id}.")
    except Exception as e:
        print(f"Error creating instance: {e}")

def available_regions():
    """사용 가능한 리전 조회"""
    print("Available regions...")
    try:
        regions = ec2.describe_regions()
        for region in regions['Regions']:
            print(f"[region] {region['RegionName']}, [endpoint] {region['Endpoint']}")
    except Exception as e:
        print(f"Error retrieving regions: {e}")

def list_images(filter_name=None, owners=['self']):
    """AMI 이미지 목록 조회"""
    print("Listing images...")
    try:
        filters = []
        if filter_name:
            filters.append({'Name': 'name', 'Values': [filter_name]})
        images = ec2.describe_images(Filters=filters, Owners=owners)
        for image in images['Images']:
            print(f"[ImageID] {image['ImageId']}, [Name] {image.get('Name', 'N/A')}, [Owner] {image['OwnerId']}, [State] {image['State']}")
    except Exception as e:
        print(f"Error listing images: {e}")

def main():
    """메인 콘솔"""
    while True:
        print("\nAWS EC2 Management")
        print("1. List instances")
        print("2. Available zones")
        print("3. Start instance")
        print("4. Available regions")
        print("5. Stop instance")
        print("6. Create instance")
        print("7. Reboot instance")
        print("8. List images")
        print("99. Quit")
        choice = input("Enter your choice: ")

        if choice == '1':
            list_instances()
        elif choice == '2':
            available_zones()
        elif choice == '3':
            instance_id = input("Enter the instance ID to start: ")
            start_instance(instance_id)
        elif choice == '4':
            available_regions()
        elif choice == '5':
            instance_id = input("Enter the instance ID to stop: ")
            stop_instance(instance_id)
        elif choice == '6':
            ami_id = input("Enter the AMI ID to create an instance: ")
            instance_type = input("Enter instance type (default: t2.micro): ") or 't2.micro'
            key_name = input("Enter key pair name (optional): ") or None
            security_group = input("Enter security group ID (optional): ") or None
            create_instance(ami_id, instance_type, key_name, security_group)
        elif choice == '7':
            instance_id = input("Enter the instance ID to reboot: ")
            reboot_instance(instance_id)
        elif choice == '8':
            filter_name = input("Enter AMI filter name (leave empty for all images): ")
            list_images(filter_name.strip() or None)
        elif choice == '99':
            print("Exiting...")
            sys.exit()
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except NoCredentialsError:
        print("AWS credentials not found. Please configure them using 'aws configure'.")
    except PartialCredentialsError:
        print("Incomplete AWS credentials found. Please check your configuration.")
