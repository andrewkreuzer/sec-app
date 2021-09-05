import json


import pulumi
import pulumi_aws as aws


def create_migrations_lambda(private_subnet_ids, vpc_id, db_host):
    migration_lambda_role = aws.iam.Role(
        "KreuzerServiceRoleForMigrationsLambda",
        name="KreuzerServiceRoleForMigrationsLambda",
        assume_role_policy=json.dumps(
            {
                "Version": "2008-10-17",
                "Statement": [
                    {
                        "Sid": "",
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        ),
    )

    iam = aws.iam.Policy(
        "policy",
        path="/",
        description="My test policy",
        policy=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": ["rds-db:connect"],
                        "Effect": "Allow",
                        "Resource": "arn:aws:rds-db:us-east-2:146427984190:dbuser:*/*",
                    }
                ],
            }
        ),
    )

    attach = aws.iam.RolePolicyAttachment(
        "KreuzerServiceRoleForMigrationsLambdaIAMAttachment",
        role=migration_lambda_role.name,
        policy_arn=iam.arn,
    )

    aws_lambda_vpc_access = aws.iam.get_policy(
        arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
    )

    attach = aws.iam.RolePolicyAttachment(
        "KreuzerServiceRoleForMigrationsLambdaAttachment",
        role=migration_lambda_role.name,
        policy_arn=aws_lambda_vpc_access.arn,
    )

    lambda_sec_group = aws.ec2.SecurityGroup(
        "allowTls",
        description="Migration lambda sec group",
        vpc_id=vpc_id,
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                from_port=0,
                to_port=0,
                protocol="-1",
                cidr_blocks=["0.0.0.0/0"],
                ipv6_cidr_blocks=["::/0"],
            )
        ],
    )

    lambda_func = aws.lambda_.Function(
        "MigrationsLambda",
        name="MigrationsLambda",
        role=migration_lambda_role.arn,
        runtime="go1.x",
        handler="migrations",
        timeout=30,
        code=pulumi.AssetArchive(
            {
                "migrations": pulumi.FileAsset("./lambda/migrations/build/migrations"),
                ".env": pulumi.FileAsset("./lambda/migrations/build/.env"),
                "migrate": pulumi.FileArchive("./lambda/migrations/build/migrate"),
            }
        ),
        environment=aws.lambda_.FunctionEnvironmentArgs(
            variables={
                "DB_HOST": db_host,
            }
        ),
        vpc_config=aws.lambda_.FunctionVpcConfigArgs(
            security_group_ids=[lambda_sec_group.id],
            subnet_ids=private_subnet_ids,
        ),
    )
