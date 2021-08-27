from pulumi import export, ResourceOptions
import pulumi_aws as aws
import json

sec_app_build_role = aws.iam.Role(
    "KreuzerServiceRoleForSecAppCodebuildBuild",
    name="KreuzerServiceRoleForSecAppCodebuildBuild",
    assume_role_policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
""",
)

sec_app_build_role_policy = aws.iam.RolePolicy(
    "sec_app_build_role_policy",
    role=sec_app_build_role.name,
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Resource": [
                        "arn:aws:logs:us-east-2:146427984190:log-group:/aws/codebuild/sec_app_build",
                        "arn:aws:logs:us-east-2:146427984190:log-group:/aws/codebuild/sec_app_build:*",
                    ],
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                    ],
                },
                {
                    "Effect": "Allow",
                    "Resource": ["arn:aws:s3:::codepipeline-us-east-2-*"],
                    "Action": [
                        "s3:PutObject",
                        "s3:GetObject",
                        "s3:GetObjectVersion",
                        "s3:GetBucketAcl",
                        "s3:GetBucketLocation",
                    ],
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "codebuild:CreateReportGroup",
                        "codebuild:CreateReport",
                        "codebuild:UpdateReport",
                        "codebuild:BatchPutTestCases",
                        "codebuild:BatchPutCodeCoverages",
                    ],
                    "Resource": [
                        "arn:aws:codebuild:us-east-2:146427984190:report-group/sec_app_build-*"
                    ],
                },
            ],
        }
    ),
)

aws_ec2_container_power_user_policy = aws.iam.get_policy(
    arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser"
)

test_attach = aws.iam.RolePolicyAttachment(
    "KreuzerServiceRoleForSecAppCodebuildBuildAttachment",
    role=sec_app_build_role.name,
    policy_arn=aws_ec2_container_power_user_policy.arn,
)

sec_app_build = aws.codebuild.Project(
    "sec_app_build",
    description="sec-app builder",
    build_timeout=5,
    service_role=sec_app_build_role.arn,
    artifacts=aws.codebuild.ProjectArtifactsArgs(
        type="CODEPIPELINE",
    ),
    environment=aws.codebuild.ProjectEnvironmentArgs(
        compute_type="BUILD_GENERAL1_SMALL",
        image="aws/codebuild/standard:1.0",
        type="LINUX_CONTAINER",
        image_pull_credentials_type="CODEBUILD",
        privileged_mode=True,
    ),
    logs_config=aws.codebuild.ProjectLogsConfigArgs(
        cloudwatch_logs=aws.codebuild.ProjectLogsConfigCloudwatchLogsArgs(
            group_name="/aws/codebuild/sec_app_build",
        ),
    ),
    source=aws.codebuild.ProjectSourceArgs(
        type="CODEPIPELINE",
    ),
)
