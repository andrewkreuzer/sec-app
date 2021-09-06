import pulumi
import pulumi_aws as aws


def create_database(vpc_private_subnet_ids, vpc_id):
    subnet_group = aws.rds.SubnetGroup("default", subnet_ids=vpc_private_subnet_ids)

    db_sec_group = aws.ec2.SecurityGroup(
        "db_sec_group",
        vpc_id=vpc_id,
        description="Enable intra VPC access",
        ingress=[
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=3306,
                to_port=3306,
                cidr_blocks=["10.0.0.0/16"],
            )
        ],
    )

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
        vpc_security_group_ids=[db_sec_group.id]
    )

    sec_app_zone = aws.route53.get_zone(
        name="sec-app.internal",
        private_zone=True
    )

    db_route = aws.route53.Record("db_route",
        name="db.sec-app.internal",
        records=[db.address],
        ttl=300,
        type="CNAME",
        zone_id="Z07288891LWDKJYRV0WZV",
    )

    return db.address
