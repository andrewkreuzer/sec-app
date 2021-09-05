import pulumi
import pulumi_aws as aws


def create_database(vpc_private_subnet_ids, vpc_id):
    subnet_group = aws.rds.SubnetGroup("default", subnet_ids=vpc_private_subnet_ids)

    db = aws.rds.Instance(
        "sec-app",
        allocated_storage=10,
        engine="mysql",
        engine_version="5.7",
        instance_class="db.t3.micro",
        name="sec_app",
        parameter_group_name="default.mysql5.7",
        password="foobarbaz",
        skip_final_snapshot=True,
        username="foo",
        db_subnet_group_name=subnet_group.name,
        iam_database_authentication_enabled=True,
    )

    return db.address
