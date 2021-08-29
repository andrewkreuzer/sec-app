from vpc import create_vpc
from codepipeline import create_code_pipeline
from codebuild import create_code_build
from cluster import create_ecs_cluster
from codedeploy import create_code_deploy

vpc_id, vpc_subnet_ids  = create_vpc()

cluster_name, service_name, tg1_name, tg2_name, wl_arn = create_ecs_cluster(
    vpc_id=vpc_id, vpc_subnets_ids=vpc_subnet_ids
)

sec_app_build_name = create_code_build()
create_code_deploy(
    cluster_name=cluster_name,
    service_name=service_name,
    tg1_name=tg1_name,
    tg2_name=tg2_name,
    wl_arn=wl_arn,
)
create_code_pipeline(sec_app_build_name=sec_app_build_name)
