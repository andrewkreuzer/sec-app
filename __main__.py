from pulumi import export, ResourceOptions
import pulumi_aws as aws
import json

from codepipeline import *
from codebuild import *

# Create an ECS cluster to run a container-based service.
cluster = aws.ecs.Cluster("cluster")

# Read back the default VPC and public subnets, which we will use.
default_vpc = aws.ec2.get_vpc(default=True)
default_vpc_subnets = aws.ec2.get_subnet_ids(vpc_id=default_vpc.id)

ecr = aws.ecr.Repository(
    "sec-app",
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True,
    ),
    image_tag_mutability="MUTABLE",
)

# Create a SecurityGroup that permits HTTP ingress and unrestricted egress.
group = aws.ec2.SecurityGroup(
    "web-secgrp",
    vpc_id=default_vpc.id,
    description="Enable HTTP access",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
)

# Create a load balancer to listen for HTTP traffic on port 80.
alb = aws.lb.LoadBalancer(
    "app-lb",
    security_groups=[group.id],
    subnets=default_vpc_subnets.ids,
)

atg1 = aws.lb.TargetGroup(
    "app-tg-1",
    port=80,
    protocol="HTTP",
    target_type="ip",
    vpc_id=default_vpc.id,
)

atg2 = aws.lb.TargetGroup(
    "app-tg-2",
    port=80,
    protocol="HTTP",
    target_type="ip",
    vpc_id=default_vpc.id,
)

wl = aws.lb.Listener(
    "web-1",
    load_balancer_arn=alb.arn,
    port=80,
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward",
            target_group_arn=atg1.arn,
        )
    ],
)

# Create an IAM role that can be used by our service's task.
role = aws.iam.Role(
    "task-exec-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2008-10-17",
            "Statement": [
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    ),
)

rpa = aws.iam.RolePolicyAttachment(
    "task-exec-policy",
    role=role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
)

# TODO: pulumi's still struggling, can't even call helper functions
# Output.concat(ecr.repository_url, ":latest")
#       you get:
#           TypeError: Object of type Output is not JSON serializable
image = "146427984190.dkr.ecr.us-east-2.amazonaws.com/sec-app-013e680:latest"

# Spin up a load balanced service running our container image.
task_definition = aws.ecs.TaskDefinition(
    "app-task",
    family="fargate-task-definition",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=role.arn,
    container_definitions=json.dumps(
        [
            {
                "name": "my-app",
                "image": image,
                "portMappings": [
                    {"containerPort": 80, "hostPort": 80, "protocol": "tcp"}
                ],
            }
        ]
    ),
)

service = aws.ecs.Service(
    "app-svc",
    cluster=cluster.arn,
    desired_count=3,
    launch_type="FARGATE",
    task_definition=task_definition.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=True,
        subnets=default_vpc_subnets.ids,
        security_groups=[group.id],
    ),
    load_balancers=[
        aws.ecs.ServiceLoadBalancerArgs(
            target_group_arn=atg1.arn,
            container_name="my-app",
            container_port=80,
        )
    ],
    opts=ResourceOptions(depends_on=[wl], ignore_changes=["task_definition"]),
)

export("url", alb.dns_name)