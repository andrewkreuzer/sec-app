import json

from pulumi import export, ResourceOptions
import pulumi_aws as aws

def create_ecs_cluster():
    cluster = aws.ecs.Cluster("sec-app", name="sec-app")

    # Read back the default VPC and public subnets, which we will use.
    default_vpc = aws.ec2.get_vpc(default=True)
    default_vpc_subnets = aws.ec2.get_subnet_ids(vpc_id=default_vpc.id)

    ecr = aws.ecr.Repository(
        "sec-app",
        name="sec-app",
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
        "sec-app-tg-1",
        port=80,
        protocol="HTTP",
        target_type="ip",
        vpc_id=default_vpc.id,
        health_check=aws.lb.TargetGroupHealthCheckArgs(
            path="/health"
        ),
    )

    atg2 = aws.lb.TargetGroup(
        "sec-app-tg-2",
        port=80,
        protocol="HTTP",
        target_type="ip",
        vpc_id=default_vpc.id,
        health_check=aws.lb.TargetGroupHealthCheckArgs(
            path="/health"
        ),
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
        "KreuzerServiceRoleForECSTaskExec",
        name="KreuzerServiceRoleForECSTaskExec",
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
        "AmazonECSTaskExecutionRolePolicyAttachment",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
    )

    image = "146427984190.dkr.ecr.us-east-2.amazonaws.com/sec-app:latest"
    task_definition = aws.ecs.TaskDefinition(
        "sec-app-task",
        family="fargate-task-definition",
        cpu="256",
        memory="512",
        network_mode="awsvpc",
        requires_compatibilities=["FARGATE"],
        execution_role_arn=role.arn,
        container_definitions=json.dumps(
            [
                {
                    "name": "sec-app",
                    "image": image,
                    "portMappings": [
                        {"containerPort": 80, "hostPort": 80, "protocol": "tcp"}
                    ],
                }
            ]
        ),
    )

    service = aws.ecs.Service(
        "sec-app",
        name="sec-app",
        cluster=cluster.arn,
        desired_count=3,
        launch_type="FARGATE",
        task_definition=task_definition.arn,
        deployment_controller=aws.ecs.ServiceDeploymentControllerArgs(type="CODE_DEPLOY"),
        network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
            assign_public_ip=True,
            subnets=default_vpc_subnets.ids,
            security_groups=[group.id],
        ),
        load_balancers=[
            aws.ecs.ServiceLoadBalancerArgs(
                target_group_arn=atg1.arn,
                container_name="sec-app",
                container_port=80,
            )
        ],
        opts=ResourceOptions(depends_on=[wl], ignore_changes=["task_definition"]),
    )

    export("url", alb.dns_name)

    return cluster.name, service.name, atg1.name, atg2.name, wl.arn

