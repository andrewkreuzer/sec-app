from vpc import create_vpc
from codepipeline import create_code_pipeline
from codebuild import create_code_build
from cluster import create_ecs_cluster
from codedeploy import create_code_deploy
from database import create_database
from secrets import create_secret
from migrations import create_migrations_lambda

vpc_id, vpc_public_subnet_ids, vpc_private_subnet_ids = create_vpc()

cluster_name, service_name, tg1_name, tg2_name, wl_arn = create_ecs_cluster(
    vpc_id=vpc_id, vpc_subnets_ids=vpc_public_subnet_ids
)

create_secret()
db_host = create_database(vpc_private_subnet_ids=vpc_private_subnet_ids, vpc_id=vpc_id)

sec_app_build_name = create_code_build()
create_code_deploy(
    cluster_name=cluster_name,
    service_name=service_name,
    tg1_name=tg1_name,
    tg2_name=tg2_name,
    wl_arn=wl_arn,
)
migrations_lambda_name = create_migrations_lambda(vpc_id=vpc_id, private_subnet_ids=vpc_private_subnet_ids, db_host=db_host)
create_code_pipeline(sec_app_build_name=sec_app_build_name, migrations_lambda_name=migrations_lambda_name)
