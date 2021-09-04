import pulumi
from pulumi.invoke import InvokeOptions
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

    availability_zones = [
        "us-east-2a",
        "us-east-2b",
        "us-east-2c",
    ]

    public_cidr = [ "10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24" ]
    private_cidr = [ "10.0.100.0/24", "10.0.200.0/24", "10.0.250.0/24" ]

    public_subnet_ids = []
    private_subnet_ids = []
    for i, az in enumerate(availability_zones):
        vpc_public_subnet = aws.ec2.Subnet(
            f"subnet_{az}_pub",
            vpc_id=vpc.id,
            cidr_block=public_cidr[i],
            availability_zone=az,
        )
        public_subnet_ids.append(vpc_public_subnet.id)

        vpc_private_subnet = aws.ec2.Subnet(
            f"subnet_{az}_priv",
            vpc_id=vpc.id,
            cidr_block=private_cidr[i],
            availability_zone=az,
        )
        private_subnet_ids.append(vpc_private_subnet.id)

    private_subnet_routes = aws.ec2.RouteTable(
        "private_subnet_routes",
        vpc_id=vpc.id,
        routes=[],
    )

    for i, subnet in enumerate(private_subnet_ids):
        route_table_association = aws.ec2.RouteTableAssociation(
            f"privateRouteTableAssociation{i}",
            subnet_id=subnet,
            route_table_id=private_subnet_routes.id,
        )

    public_subnet_routes = aws.ec2.RouteTable(
        "public_subnet_routes",
        vpc_id=vpc.id,
        routes=[
            aws.ec2.RouteTableRouteArgs(
                cidr_block="0.0.0.0/0",
                gateway_id=igw.id,
            ),
        ],
    )

    for i, subnet in enumerate(public_subnet_ids):
        route_table_association = aws.ec2.RouteTableAssociation(
            f"publicRouteTableAssociation{i}",
            subnet_id=subnet,
            route_table_id=public_subnet_routes.id,
        )

    return vpc.id, public_subnet_ids, private_subnet_ids
