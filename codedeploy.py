import pulumi
import pulumi_aws as aws

sec_app = aws.codedeploy.Application(
    "sec-app",
    compute_platform="ECS",
    name="sec-app",
    opts=pulumi.ResourceOptions(protect=True),
)


sec_app = aws.codedeploy.DeploymentGroup(
    "sec-app",
    app_name="sec-app",
    deployment_config_name="CodeDeployDefault.ECSAllAtOnce",
    deployment_group_name="sec-app",
    ecs_service=aws.codedeploy.DeploymentGroupEcsServiceArgs(
        cluster_name="sec-app",
        service_name="sec-app",
    ),
    deployment_style=aws.codedeploy.DeploymentGroupDeploymentStyleArgs(
        deployment_option="WITH_TRAFFIC_CONTROL",
        deployment_type="BLUE_GREEN",
    ),
    blue_green_deployment_config=aws.codedeploy.DeploymentGroupBlueGreenDeploymentConfigArgs(
        deployment_ready_option=aws.codedeploy.DeploymentGroupBlueGreenDeploymentConfigDeploymentReadyOptionArgs(
            action_on_timeout="CONTINUE_DEPLOYMENT",
        ),
        terminate_blue_instances_on_deployment_success=aws.codedeploy.DeploymentGroupBlueGreenDeploymentConfigTerminateBlueInstancesOnDeploymentSuccessArgs(
            action="TERMINATE",
            termination_wait_time_in_minutes=5,
        ),
    ),
    load_balancer_info=aws.codedeploy.DeploymentGroupLoadBalancerInfoArgs(
        target_group_pair_info=aws.codedeploy.DeploymentGroupLoadBalancerInfoTargetGroupPairInfoArgs(
            prod_traffic_route=aws.codedeploy.DeploymentGroupLoadBalancerInfoTargetGroupPairInfoProdTrafficRouteArgs(
                listener_arns=[
                    "arn:aws:elasticloadbalancing:us-east-2:146427984190:listener/app/app-lb-0d4e337/8ce076de4d0904a1/4a280847c7f47ad8"
                ],
            ),
            target_groups=[
                aws.codedeploy.DeploymentGroupLoadBalancerInfoTargetGroupPairInfoTargetGroupArgs(
                    name="app-tg-1-8a71961",
                ),
                aws.codedeploy.DeploymentGroupLoadBalancerInfoTargetGroupPairInfoTargetGroupArgs(
                    name="app-tg-2-862fea0",
                ),
            ],
        ),
    ),
    service_role_arn="arn:aws:iam::146427984190:role/KreuzerServiceRoleForCodeDeployECS",
    opts=pulumi.ResourceOptions(protect=True),
)
