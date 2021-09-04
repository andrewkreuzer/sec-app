import pulumi
import pulumi_aws as aws


def create_secret():
    db_password = aws.secretsmanager.Secret("db_password")
