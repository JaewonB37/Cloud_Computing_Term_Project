import boto3
import sys
import subprocess
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import paramiko
from colorama import Fore, Style, init
from datetime import datetime, timedelta, timezone

# 초기화 (Windows에서도 색상 출력 활성화)
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
def list_images(filter_name=None):
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
        
# 10. 알람 조회
def list_alarms():
    print("Listing alarms...")
    try:
        alarms = cloudwatch.describe_alarms()
        for alarm in alarms['MetricAlarms']:
            print(f"[Alarm Name] {alarm['AlarmName']}, [State] {alarm['StateValue']}, [Metric] {alarm['MetricName']}")
    except Exception as e:
        print(f"Error listing alarms: {e}")
        
# 11. 알람 생성
def create_alarm():
    print("Creating alarm...")
    try:
        response = cloudwatch.put_metric_alarm(
            AlarmName='my-alarm',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=1,
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',
            Period=60,
            Statistic='Average',
            Threshold=70.0,
            ActionsEnabled=False,
            AlarmDescription='Alarm when server CPU exceeds 70%',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': 'i-032fce4eb5d67655b'
                },
            ],
            Unit='Percent'
        )
        print("Successfully created alarm.")
    except Exception as e:
        print(f"Error creating alarm: {e}")
        
# 12. 알람 삭제
def delete_alarm(alarm_name):
    print(f"Deleting alarm {alarm_name}...")
    try:
        cloudwatch.delete_alarms(AlarmNames=[alarm_name])
        print(f"Successfully deleted alarm {alarm_name}.")
    except Exception as e:
        print(f"Error deleting alarm: {e}")
        
# 13. 메트릭 목록 조회
def list_metrics():
    print("Listing metrics...")
    try:
        metrics = cloudwatch.list_metrics()
        for metric in metrics['Metrics']:
            print(f"[Namespace] {metric['Namespace']}, [Metric Name] {metric['MetricName']}")
    except Exception as e:
        print(f"Error listing metrics: {e}")
        
# 14. 메트릭 통계 조회
def get_metric_statistics():
    print("Getting metric statistics...")
    try:
        # 현재 시간 기준으로 시간 범위 설정 (마지막 24시간)
        end_time = datetime.now(timezone.utc)  # 현재 시간(UTC)
        start_time = end_time - timedelta(hours=6)  # 6시간 데이터 조회

        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': 'i-12345678'  # 실제 인스턴스 ID로 변경
                },
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,  # 5분 단위로 데이터 그룹화
            Statistics=['Average'],
            Unit='Percent'
        )
        
        # 결과 출력
        print("Metric statistics retrieved successfully:")
        for datapoint in response['Datapoints']:
            timestamp = datapoint['Timestamp']
            average = datapoint['Average']
            print(f"Timestamp: {timestamp}, Average: {average}")
    except Exception as e:
        print(f"Error getting metric statistics: {e}")
        
# 15. 메트릭 알람 목록 조회
def list_metric_alarms():
    print("Listing metric alarms...")
    try:
        alarms = cloudwatch.describe_alarms_for_metric(
            MetricName='CPUUtilization',
            Namespace='AWS/EC2'
        )
        for alarm in alarms['MetricAlarms']:
            print(f"[Alarm Name] {alarm['AlarmName']}, [State] {alarm['StateValue']}")
    except Exception as e:
        print(f"Error listing metric alarms: {e}")
        
# CloudWatch Logs 클라이언트 초기화
logs = boto3.client('logs', region_name='ap-northeast-2')

# 16. 메트릭 필터 목록 조회
def list_metric_filters():
    print("Listing metric filters...")
    try:
        log_group_name = input("Enter log group name: ").strip()
        if not log_group_name:
            print("Log group name cannot be empty.")
            return
        response = logs.describe_metric_filters(logGroupName=log_group_name)
        metric_filters = response.get('metricFilters', [])
        if not metric_filters:
            print(f"No metric filters found for log group {log_group_name}.")
        for metric_filter in metric_filters:
            print(f"[Filter Name] {metric_filter['filterName']}, [Pattern] {metric_filter['filterPattern']}")
    except Exception as e:
        print(f"Error listing metric filters: {e}")

# 17. 메트릭 필터 추가
def put_metric_filter():
    print("Putting metric filter...")
    try:
        log_group_name = input("Enter log group name: ").strip()
        if not log_group_name:
            print("Log group name cannot be empty.")
            return
        response = logs.put_metric_filter(
            logGroupName=log_group_name,
            filterName='my-metric-filter',
            filterPattern='ERROR',
            metricTransformations=[
                {
                    'metricName': 'ErrorCount',
                    'metricNamespace': 'MyNamespace',
                    'metricValue': '1'
                }
            ]
        )
        print("Successfully created metric filter.")
    except Exception as e:
        print(f"Error putting metric filter: {e}")

# 18. 메트릭 필터 삭제
def delete_metric_filter(filter_name):
    print(f"Deleting metric filter {filter_name}...")
    try:
        log_group_name = input("Enter log group name: ").strip()
        if not log_group_name:
            print("Log group name cannot be empty.")
            return
        logs.delete_metric_filter(logGroupName=log_group_name, filterName=filter_name)
        print(f"Successfully deleted metric filter {filter_name}.")
    except Exception as e:
        print(f"Error deleting metric filter: {e}")

        
        
# 19. 알람 이력 조회
def describe_alarm_history():
    print("Describing alarm history...")
    try:
        history = cloudwatch.describe_alarm_history()
        for event in history['AlarmHistoryItems']:
            print(f"[Alarm Name] {event['AlarmName']}, [Timestamp] {event['Timestamp']}")
    except Exception as e:
        print(f"Error describing alarm history: {e}")

# 메인 함수
def main():
    while True:
        print("------------------------------------------------------------")
        print("           Amazon AWS Control Panel using SDK               ")
        print("------------------------------------------------------------")
        print("  1. List instances                2. Available zones")
        print("  3. Start instance                4. Available regions")
        print("  5. Stop instance                 6. Create instance")
        print("  7. Reboot instance               8. List images")
        print("  9. Execute 'condor_status'")
        print("------------------------------------------------------------")
        # Cloud Watch
        print(" 10. List alarms                   11. Create alarm")
        print(" 12. Delete alarm                  13. List metrics")
        print(" 14. Get metric statistics         15. List metric alarms")
        print(" 16. List metric filters           17. Put metric filter")
        print(" 18. Delete metric filter          19. Describe alarm history")
        print("------------------------------------------------------------")        
        print("                                 99. Quit")
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
            filter_name = "aws-jaewon-slave"
            list_images(filter_name.strip() or None)
        elif choice == '9':
            instance_id = "i-032fce4eb5d67655b"
            condor_status(instance_id)
        elif choice == '10':
            list_alarms()
        elif choice == '11':
            create_alarm()
        elif choice == '12':
            alarm_name = input("Enter alarm name to delete: ")
            delete_alarm(alarm_name)
        elif choice == '13':
            list_metrics()
        elif choice == '14':
            get_metric_statistics()
        elif choice == '15':
            list_metric_alarms()
        elif choice == '16':
            list_metric_filters()
        elif choice == '17':
            put_metric_filter()
        elif choice == '18':
            filter_name = input("Enter filter name to delete: ")
            delete_metric_filter(filter_name)
        elif choice == '19':
            describe_alarm_history()
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
