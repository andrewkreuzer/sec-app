import pulumi
import pulumi_aws as aws


def create_vpc():
    # Read back the default VPC and public subnets, which we will use.
    vpc = aws.ec2.Vpc(
        "sec-app",
        cidr_block="10.0.0.0/16",
        enable_dns_hostnames=True,
        enable_dns_support=True,
    )

    igw = aws.ec2.InternetGateway(
        "gw",
        vpc_id=vpc.id,
    )

    route_table = aws.ec2.get_route_table(route_table_id=vpc.main_route_table_id)
    igw_route = aws.ec2.Route("igw_route",
        route_table_id=route_table.id,
        destination_cidr_block="0.0.0.0/0",
        gateway_id=igw.id
    )

    availability_zones = [
        "us-east-2a",
        "us-east-2b",
        "us-east-2c",
    ]

    subnet_ids = []
    for i, az in enumerate(availability_zones):
        vpc_subnet_1 = aws.ec2.Subnet(
            f"subnet_{az}_1",
            vpc_id=vpc.id,
            cidr_block=f"10.0.{i+1}.0/24",
            availability_zone=az,
        )

        subnet_ids.append(vpc_subnet_1.id)

        # vpc_subnet_2 = aws.ec2.Subnet(
        #     f"subnet_{az}_2",
        #     vpc_id=vpc.id,
        #     cidr_block="10.0.2.0/24",
        #     availability_zone=az
        # )


    return vpc.id, subnet_ids
