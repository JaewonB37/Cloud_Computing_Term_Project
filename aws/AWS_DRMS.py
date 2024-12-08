import boto3
import sys
import json
import subprocess
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import paramiko
from colorama import Fore, Style, init
from datetime import datetime, timedelta, timezone
from pytz import timezone as pytz_timezone

init()

# AWS 클라이언트 초기화
ec2 = boto3.client('ec2', region_name='ap-northeast-2')

# 상태 색상 정의
def color_state(state):
    if state.lower() == "running":
        return f"{Fore.GREEN}{state}{Style.RESET_ALL}"
    elif state.lower() == "stopped":
        return f"{Fore.RED}{state}{Style.RESET_ALL}"
    elif state.lower() == "pending":
        return f"{Fore.YELLOW}{state}{Style.RESET_ALL}"
    else:
        return state

# 1. EC2 인스턴스 목록 조회
def list_instances():
    print(f"Listing instances...")
    try:
        instances = ec2.describe_instances()
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                state = color_state(instance['State']['Name'])
                print(f"[ID] {instance['InstanceId']}, "
                      f"[AMI] {instance['ImageId']}, "
                      f"[Type] {instance['InstanceType']}, "
                      f"[State] {state}, "
                      f"[Public IP] {instance.get('PublicIpAddress', 'N/A')}, "
                      f"[Tags] {instance.get('Tags', 'None')}")
    except Exception as e:
        print(f"Error listing instances: {e}")

# 2. 사용 가능한 가용 영역 조회
def available_zones():
    print(f"Available zones...")
    try:
        zones = ec2.describe_availability_zones()
        for zone in zones['AvailabilityZones']:
            print(f"[Zone ID] {zone['ZoneId']}, [Region] {zone['RegionName']}, [Zone Name] {zone['ZoneName']}")
    except Exception as e:
        print(f"Error retrieving availability zones: {e}")

# 3. 인스턴스 시작
def start_instance(instance_id):
    print(f"Starting instance {instance_id}...")
    try:
        response = ec2.start_instances(InstanceIds=[instance_id])
        for instance in response['StartingInstances']:
            state = color_state(instance['CurrentState']['Name'])
            print(f"Instance {instance['InstanceId']} is now {state}.")
    except Exception as e:
        print(f"Error starting instance: {e}")

# 4. 사용 가능한 리전 조회
def available_regions():
    print(f"Available regions...")
    try:
        regions = ec2.describe_regions()
        for region in regions['Regions']:
            print(f"[Region] {region['RegionName']}, [Endpoint] {region['Endpoint']}")
    except Exception as e:
        print(f"Error retrieving regions: {e}")

# 5. 인스턴스 중지
def stop_instance(instance_id):
    print(f"Stopping instance {instance_id}...")
    try:
        response = ec2.stop_instances(InstanceIds=[instance_id])
        for instance in response['StoppingInstances']:
            state = color_state(instance['CurrentState']['Name'])
            print(f"Instance {instance['InstanceId']} is now {state}.")
    except Exception as e:
        print(f"Error stopping instance: {e}")

# 6. 인스턴스 생성
def create_instance(ami_id):
    print(f"Creating instance with AMI {ami_id}...")
    try:
        response = ec2.run_instances(
            ImageId=ami_id,
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1
        )
        instance_id = response['Instances'][0]['InstanceId']
        print(f"Successfully started EC2 instance {instance_id} based on AMI {ami_id}.")
    except Exception as e:
        print(f"Error creating instance: {e}")

# 7. 인스턴스 재부팅
def reboot_instance(instance_id):
    print(f"Rebooting instance {instance_id}...")
    try:
        ec2.reboot_instances(InstanceIds=[instance_id])
        print(f"Successfully rebooted instance {instance_id}.")
    except Exception as e:
        print(f"Error rebooting instance: {e}")

# 8. AMI 이미지 목록 조회
def list_images(filter_name):
    print(f"Listing images...")
    try:
        filters = []
        if filter_name:
            filters.append({'Name': 'name', 'Values': [filter_name]})
        images = ec2.describe_images(Filters=filters)
        for image in images['Images']:
            print(f"[ImageID] {image['ImageId']}, [Name] {image.get('Name', 'N/A')}, [Owner] {image['OwnerId']}")
    except Exception as e:
        print(f"Error listing images: {e}")

# 9. HTCondor 상태 조회
def condor_status(instance_id):
    command = "condor_status"
    print(f"Executing '{command}' on instance {instance_id}...")
    try:
        instance = ec2.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]
        public_ip = instance.get('PublicIpAddress')
        if not public_ip:
            print("Error: Instance does not have a public IP address.")
            return
        ssh_key_path = "../cloud-test.pem"
        username = "ec2-user"
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(public_ip, username=username, key_filename=ssh_key_path)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        if output:
            print("Command output:")
            print(output)
        if error:
            print("Command error:")
            print(error)
        ssh.close()
    except Exception as e:
        print(f"Error executing SSH command: {e}")
        
# CloudWatch 클라이언트 초기화
cloudwatch = boto3.client('cloudwatch', region_name='ap-northeast-2')
sns = boto3.client('sns', region_name='ap-northeast-2')
        
# 10. 경보 목록 출력
def list_alarms():
    print("Listing alarms...")
    try:
        alarms = cloudwatch.describe_alarms()
        for alarm in alarms['MetricAlarms']:
            print(f"[Alarm Name] {alarm['AlarmName']}, [State] {alarm['StateValue']}, [Metric] {alarm['MetricName']}")
    except Exception as e:
        print(f"Error listing alarms: {e}")
        
# 11-1. CPU Utilization 경보 생성
def create_cpu_alarm():
    print("Creating alarm with email notification...")
    try:
        # SNS 주제 생성
        sns_topic_name = "CloudWatch_Alarms_Topic"
        response = sns.create_topic(Name=sns_topic_name)
        sns_topic_arn = response['TopicArn']  # SNS 주제 ARN
        
        # 이메일 주소를 SNS 주제에 구독
        email = "bjo3079@gmail.com"
        sns.subscribe(TopicArn=sns_topic_arn, Protocol='email', Endpoint=email)
        print(f"Subscribed emails to SNS topic: {sns_topic_arn}")
        print("Please confirm email subscriptions via the confirmation email sent to each address.")

        # CloudWatch 알람 생성
        cloudwatch.put_metric_alarm(
            AlarmName='master-cpu-alarm',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=1,
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',
            Period=60,
            Statistic='Average',
            Threshold=30.0,
            ActionsEnabled=True,  # 알림 활성화
            AlarmDescription='Alarm when server CPU exceeds 30%',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': 'i-032fce4eb5d67655b'
                },
            ],
            Unit='Percent',
            AlarmActions=[sns_topic_arn]  # SNS 주제와 연결
        )
        print("Successfully created alarm with email notifications.")
    except Exception as e:
        print(f"Error creating alarm with email notification: {e}")
        
# 11-2. 네트워크 트래픽 경보 생성
def create_network_alarm():
    print("Creating network alarm with email notification...")
    try:
        # SNS 주제 생성
        sns_topic_name = "Network_Alarms_Topic"
        response = sns.create_topic(Name=sns_topic_name)
        sns_topic_arn = response['TopicArn']  # SNS 주제 ARN

        # 이메일 주소를 SNS 주제에 구독
        email = "bjo3079@gmail.com"
        sns.subscribe(TopicArn=sns_topic_arn, Protocol='email', Endpoint=email)
        print(f"Subscribed emails to SNS topic: {sns_topic_arn}")
        print("Please confirm email subscriptions via the confirmation email sent to each address.")

        # CloudWatch 네트워크 트래픽 알람 생성
        cloudwatch.put_metric_alarm(
            AlarmName='master-network-in-alarm',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=1,
            MetricName='NetworkIn',
            Namespace='AWS/EC2',
            Period=60,
            Statistic='Average',
            Threshold=5000000.0,
            ActionsEnabled=True,
            AlarmDescription='Alarm when network in exceeds 5MB',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': 'i-032fce4eb5d67655b'
                },
            ],
            Unit='Bytes',
            AlarmActions=[sns_topic_arn]
        )
        print("Successfully created network alarm with email notifications.")
    except Exception as e:
        print(f"Error creating network alarm with email notification: {e}")
        
# 12. 경보 삭제
def delete_alarm(choice):
    if choice == '1':
        alarm_name = 'master-cpu-alarm'
    elif choice == '2':
        alarm_name = 'master-network-in-alarm'
    else:
        print("Invalid choice. Please select '1' or '2'.")
        return

    print(f"Deleting alarm {alarm_name}...")
    try:
        cloudwatch.delete_alarms(AlarmNames=[alarm_name])
        print(f"Successfully deleted alarm {alarm_name}.")
    except Exception as e:
        print(f"Error deleting alarm: {e}")

        
# 서울 시간대 정의
seoul_tz = pytz_timezone('Asia/Seoul')

# 13. 메트릭 통계 조회
def get_metric_statistics(choice):
    print("Getting metric statistics (Seoul Time)...")
    try:
        # 현재 시간 기준으로 시간 범위 설정 (마지막 6시간)
        end_time_utc = datetime.now(timezone.utc)  # 현재 시간(UTC)
        start_time_utc = end_time_utc - timedelta(hours=6)  # 6시간 데이터 조회

        metric_name = 'CPUUtilization' if choice == '1' else 'NetworkIn'
        unit = 'Percent' if choice == '1' else 'Bytes'

        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName=metric_name,
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': 'i-032fce4eb5d67655b'  # 실제 인스턴스 ID로 변경
                },
            ],
            StartTime=start_time_utc,  # AWS API는 UTC만 지원
            EndTime=end_time_utc,
            Period=300,  # 5분 단위로 데이터 그룹화
            Statistics=['Average'],
            Unit=unit
        )

        # 결과 출력 (서울 시간으로 변환된 시간 표시)
        if not response['Datapoints']:
            print(f"No data points found for metric {metric_name} in the last 6 hours.")
        else:
            print("Metric statistics retrieved successfully:")
            for datapoint in response['Datapoints']:
                timestamp_utc = datapoint['Timestamp']  # UTC 시간
                timestamp_seoul = timestamp_utc.astimezone(seoul_tz)  # 서울 시간으로 변환
                average = datapoint['Average']
                print(f"Timestamp (Seoul Time): {timestamp_seoul}, Average: {average}")
    except Exception as e:
        print(f"Error getting metric statistics: {e}")

# 14. 메트릭 알람 목록 조회
def list_metric_alarms(choice):
    print("Listing alarms...")
    try:
        if choice == '1':
            alarm_name_filter = 'master-cpu-alarm'
        elif choice == '2':
            alarm_name_filter = 'master-network-in-alarm'
        else:
            print("Invalid choice. Please select '1' or '2'.")
            return

        alarms = cloudwatch.describe_alarms()

        for alarm in alarms.get('MetricAlarms', []):
            if alarm['AlarmName'] == alarm_name_filter:
                print(json.dumps(alarm, indent=4, default=str))
                return

        print(f"No alarms found with the name '{alarm_name_filter}'.")
    
    except Exception as e:
        print(f"Error listing alarms: {e}")
        
# 15. 경보 이력 조회 (서울 시간으로 변환)
def describe_alarm_history(choice):
    print("Describing alarm history (Seoul Time)...")
    try:
        history = cloudwatch.describe_alarm_history() 
        alarm_events = history.get('AlarmHistoryItems', [])

        if choice == '1':
            alarm_name_filter = 'master-cpu-alarm'
        elif choice == '2':
            alarm_name_filter = 'master-network-in-alarm'
        else:
            print("Invalid choice. Please select '1' or '2'.")
            return
            
        for event in alarm_events:
            if event['HistoryItemType'] == 'StateUpdate':
                if alarm_name_filter in event['AlarmName']: 
                    timestamp_utc = event['Timestamp']
                    timestamp_seoul = timestamp_utc.astimezone(seoul_tz)
                    print(f"[Alarm Name] {event['AlarmName']}, [Timestamp (Seoul Time)]: {timestamp_seoul}, [Summary]: {event['HistorySummary']}")
    except Exception as e:
        print(f"Error describing alarm history: {e}")

# 메인 함수
def main():
    while True:
        print("-------------------------------------------------------------")
        print("           Amazon AWS Control Panel using SDK               ")
        print("-------------------------------------------------------------")
        print("  1. List instances                2. Available zones")
        print("  3. Start instance                4. Available regions")
        print("  5. Stop instance                 6. Create instance")
        print("  7. Reboot instance               8. List images")
        print("  9. Execute 'condor_status'")
        print("-------------------------------------------------------------")
        # Cloud Watch
        print(" 10. List alarms                   11. Create alarm")
        print(" 12. Delete alarm                  13. Get metric statistics")
        print(" 14. List metric alarms            15. Describe alarm history")
        print("-------------------------------------------------------------")        
        print("                                   99. Quit")
        print("-------------------------------------------------------------")  
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
            create_instance(ami_id)
        elif choice == '7':
            instance_id = input("Enter the instance ID to reboot: ")
            reboot_instance(instance_id)
        elif choice == '8':
            list_images("aws-jaewon-slave")
        elif choice == '9':
            instance_id = "i-032fce4eb5d67655b"
            condor_status(instance_id)
        elif choice == '10':
            list_alarms()
        elif choice == '11':
            metric_choice = input("Enter 1 for CPU or 2 for Network: ")
            if metric_choice == '1':
                create_cpu_alarm()
            elif metric_choice == '2':
                create_network_alarm()
            else:
                print("Invalid choice.")
        elif choice == '12':
            alarm_choice = input("Enter 1 for CPU or 2 for Network: ")
            delete_alarm(alarm_choice)
        elif choice == '13':
            metric_choice = input("Enter 1 for CPU or 2 for Network: ")
            get_metric_statistics(metric_choice)
        elif choice == '14':
            metric_choice = input("Enter 1 for CPU or 2 for Network: ")
            list_metric_alarms(metric_choice)
        elif choice == '15':
            metric_choice = input("Enter 1 for CPU or 2 for Network: ")
            describe_alarm_history(metric_choice)
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
