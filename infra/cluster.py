import json

from pulumi import export, ResourceOptions, Output
import pulumi_aws as aws


def create_ecs_cluster(vpc_id, vpc_subnets_ids):
    cluster = aws.ecs.Cluster("sec-app", name="sec-app")

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
        vpc_id=vpc_id,
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
        subnets=vpc_subnets_ids,
    )

    atg1 = aws.lb.TargetGroup(
        "sec-app-tg-1",
        port=80,
        protocol="HTTP",
        target_type="ip",
        vpc_id=vpc_id,
        health_check=aws.lb.TargetGroupHealthCheckArgs(path="/health"),
    )

    atg2 = aws.lb.TargetGroup(
        "sec-app-tg-2",
        port=80,
        protocol="HTTP",
        target_type="ip",
        vpc_id=vpc_id,
        health_check=aws.lb.TargetGroupHealthCheckArgs(path="/health"),
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

    cloudwatch_logging = aws.iam.RolePolicy(
        "cloudwatch_logging",
        role=role.name,
        policy=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:*",
                        ],
                        "Resource": [
                            "*",
                        ],
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents",
                        ],
                        "Resource": [
                            "arn:aws:logs:us-east-2:146427984190:log-group:/ecs/fargate/sec-app",
                            "arn:aws:logs:us-east-2:146427984190:log-group:/ecs/fargate/sec-app:*"
                        ],
                    }
                ],
            }
        ),
    )

    iam_db_auth = aws.iam.RolePolicy(
        "iam_db_auth_role_policy",
        role=role.name,
        policy=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["rds-db:connect"],
                        "Resource": [
                            "arn:aws:rds-db:us-east-2:146427984190:dbuser:*/*"
                        ],
                    }
                ],
            }
        ),
    )

    ecs_log_group = aws.cloudwatch.LogGroup(
        "ecs_logs",
        name="/ecs/fargate/sec-app"
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
                    "logConfiguration": { 
                      "logDriver": "awslogs",
                      "options": { 
                          "awslogs-group" : "/ecs/farget/sec-app",
                         "awslogs-region": "us-east-2",
                         "awslogs-stream-prefix": "ecs"
                      }
                   }
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
        deployment_controller=aws.ecs.ServiceDeploymentControllerArgs(
            type="CODE_DEPLOY"
        ),
        network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
            assign_public_ip=True,
            subnets=vpc_subnets_ids,
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
