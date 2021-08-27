import json

import pulumi
import pulumi_aws as aws

import codebuild

service_role_for_code_pipeline = aws.iam.Role(
    "KreuzerServiceRoleForCodePipeline",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "codepipeline.amazonaws.com",
                    },
                }
            ],
        }
    ),
    force_detach_policies=False,
    max_session_duration=3600,
    name="KreuzerServiceRoleForCodePipeline",
    path="/service-role/",
)

codepipeline_policy = aws.iam.Policy(
    "codepipeline_policy",
    description="Policy used in trust relationship with CodePipeline",
    name="AWSCodePipelineServiceRole-us-east-2-sec-app",
    path="/service-role/",
    policy="""{
    "Statement": [
        {
            "Action": [
                "iam:PassRole"
            ],
            "Resource": "*",
            "Effect": "Allow",
            "Condition": {
                "StringEqualsIfExists": {
                    "iam:PassedToService": [
                        "cloudformation.amazonaws.com",
                        "elasticbeanstalk.amazonaws.com",
                        "ec2.amazonaws.com",
                        "ecs-tasks.amazonaws.com"
                    ]
                }
            }
        },
        {
            "Action": [
                "codecommit:CancelUploadArchive",
                "codecommit:GetBranch",
                "codecommit:GetCommit",
                "codecommit:GetRepository",
                "codecommit:GetUploadArchiveStatus",
                "codecommit:UploadArchive"
            ],
            "Resource": "*",
            "Effect": "Allow"
        },
        {
            "Action": [
                "codedeploy:CreateDeployment",
                "codedeploy:GetApplication",
                "codedeploy:GetApplicationRevision",
                "codedeploy:GetDeployment",
                "codedeploy:GetDeploymentConfig",
                "codedeploy:RegisterApplicationRevision"
            ],
            "Resource": "*",
            "Effect": "Allow"
        },
        {
            "Action": [
                "codestar-connections:UseConnection"
            ],
            "Resource": "*",
            "Effect": "Allow"
        },
        {
            "Action": [
                "elasticbeanstalk:*",
                "ec2:*",
                "elasticloadbalancing:*",
                "autoscaling:*",
                "cloudwatch:*",
                "s3:*",
                "sns:*",
                "cloudformation:*",
                "rds:*",
                "sqs:*",
                "ecs:*"
            ],
            "Resource": "*",
            "Effect": "Allow"
        },
        {
            "Action": [
                "lambda:InvokeFunction",
                "lambda:ListFunctions"
            ],
            "Resource": "*",
            "Effect": "Allow"
        },
        {
            "Action": [
                "opsworks:CreateDeployment",
                "opsworks:DescribeApps",
                "opsworks:DescribeCommands",
                "opsworks:DescribeDeployments",
                "opsworks:DescribeInstances",
                "opsworks:DescribeStacks",
                "opsworks:UpdateApp",
                "opsworks:UpdateStack"
            ],
            "Resource": "*",
            "Effect": "Allow"
        },
        {
            "Action": [
                "cloudformation:CreateStack",
                "cloudformation:DeleteStack",
                "cloudformation:DescribeStacks",
                "cloudformation:UpdateStack",
                "cloudformation:CreateChangeSet",
                "cloudformation:DeleteChangeSet",
                "cloudformation:DescribeChangeSet",
                "cloudformation:ExecuteChangeSet",
                "cloudformation:SetStackPolicy",
                "cloudformation:ValidateTemplate"
            ],
            "Resource": "*",
            "Effect": "Allow"
        },
        {
            "Action": [
                "codebuild:BatchGetBuilds",
                "codebuild:StartBuild",
                "codebuild:BatchGetBuildBatches",
                "codebuild:StartBuildBatch"
            ],
            "Resource": "*",
            "Effect": "Allow"
        },
        {
            "Effect": "Allow",
            "Action": [
                "devicefarm:ListProjects",
                "devicefarm:ListDevicePools",
                "devicefarm:GetRun",
                "devicefarm:GetUpload",
                "devicefarm:CreateUpload",
                "devicefarm:ScheduleRun"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "servicecatalog:ListProvisioningArtifacts",
                "servicecatalog:CreateProvisioningArtifact",
                "servicecatalog:DescribeProvisioningArtifact",
                "servicecatalog:DeleteProvisioningArtifact",
                "servicecatalog:UpdateProduct"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:ValidateTemplate"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ecr:DescribeImages"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "states:DescribeExecution",
                "states:DescribeStateMachine",
                "states:StartExecution"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "appconfig:StartDeployment",
                "appconfig:StopDeployment",
                "appconfig:GetDeployment"
            ],
            "Resource": "*"
        }
    ],
    "Version": "2012-10-17"
}""",
)

codepipeline_policy_attachment = aws.iam.RolePolicyAttachment(
    "codepipeline_policy_attachment",
    policy_arn=codepipeline_policy.arn,
    role=service_role_for_code_pipeline.name,
)


github_connection = aws.codestarconnections.Connection("github", name="github")
sec_app = aws.codepipeline.Pipeline(
    "sec-app",
    artifact_store=aws.codepipeline.PipelineArtifactStoreArgs(
        location="codepipeline-us-east-2-141992872046",
        region="",
        type="S3",
    ),
    name="sec-app",
    role_arn=service_role_for_code_pipeline.arn,
    stages=[
        aws.codepipeline.PipelineStageArgs(
            actions=[
                aws.codepipeline.PipelineStageActionArgs(
                    category="Source",
                    configuration={
                        "BranchName": "main",
                        "ConnectionArn": github_connection.arn,
                        "FullRepositoryId": "andrewkreuzer/sec-app",
                        "OutputArtifactFormat": "CODE_ZIP",
                    },
                    input_artifacts=[],
                    name="Source",
                    namespace="SourceVariables",
                    output_artifacts=["SourceArtifact"],
                    owner="AWS",
                    provider="CodeStarSourceConnection",
                    region="us-east-2",
                    role_arn="",
                    run_order=1,
                    version="1",
                )
            ],
            name="Source",
        ),
        aws.codepipeline.PipelineStageArgs(
            actions=[
                aws.codepipeline.PipelineStageActionArgs(
                    category="Build",
                    configuration={
                        "ProjectName": codebuild.sec_app_build.name,
                    },
                    input_artifacts=["SourceArtifact"],
                    name="Build",
                    namespace="BuildVariables",
                    output_artifacts=["BuildArtifact"],
                    owner="AWS",
                    provider="CodeBuild",
                    region="us-east-2",
                    role_arn="",
                    run_order=1,
                    version="1",
                )
            ],
            name="Build",
        ),
        aws.codepipeline.PipelineStageArgs(
            actions=[
                aws.codepipeline.PipelineStageActionArgs(
                    category="Approval",
                    configuration={},
                    input_artifacts=[],
                    name="approval",
                    namespace="",
                    output_artifacts=[],
                    owner="AWS",
                    provider="Manual",
                    region="us-east-2",
                    role_arn="",
                    run_order=1,
                    version="1",
                )
            ],
            name="approval",
        ),
    ],
)