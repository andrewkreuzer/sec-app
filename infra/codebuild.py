import pulumi_aws as aws
import json


def create_code_build():
    sec_app_build_role = aws.iam.Role(
        "KreuzerServiceRoleForSecAppCodebuildBuild",
        name="KreuzerServiceRoleForSecAppCodebuildBuild",
        assume_role_policy=json.dumps(
            {
                "Version": "2008-10-17",
                "Statement": [
                    {
                        "Sid": "",
                        "Effect": "Allow",
                        "Principal": {"Service": "codebuild.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        ),
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

    test_attach = aws.iam.RolePolicyAttachment(
        "KreuzerServiceRoleForSecAppCodebuildBuildAttachment",
        role=sec_app_build_role.name,
        policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser",
    )

    sec_app_build = aws.codebuild.Project(
        "sec_app_build",
        name="sec_app_build",
        description="sec-app builder",
        build_timeout=5,
        service_role=sec_app_build_role.arn,
        artifacts=aws.codebuild.ProjectArtifactsArgs(
            type="CODEPIPELINE",
        ),
        cache=aws.codebuild.ProjectCacheArgs(
            type="LOCAL",
            modes=[
                "LOCAL_DOCKER_LAYER_CACHE",
                "LOCAL_SOURCE_CACHE",
            ],
        ),
        environment=aws.codebuild.ProjectEnvironmentArgs(
            compute_type="BUILD_GENERAL1_SMALL",
            image="aws/codebuild/standard:5.0",
            type="LINUX_CONTAINER",
            image_pull_credentials_type="CODEBUILD",
            privileged_mode=True,
            environment_variables=[
                aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                    name="REPO", value="146427984190.dkr.ecr.us-east-2.amazonaws.com"
                ),
                aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                    name="IMAGE", value="sec-app"
                ),
            ],
        ),
        logs_config=aws.codebuild.ProjectLogsConfigArgs(
            cloudwatch_logs=aws.codebuild.ProjectLogsConfigCloudwatchLogsArgs(
                group_name="/aws/codebuild/sec_app_build",
            ),
        ),
        source=aws.codebuild.ProjectSourceArgs(
            type="CODEPIPELINE", buildspec="infra/buildspec.yml"
        ),
    )

    return sec_app_build.name
