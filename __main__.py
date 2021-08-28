from codepipeline import create_code_pipeline
from codebuild import create_code_build
from cluster import create_ecs_cluster
from codedeploy import create_code_deploy

# Create an ECS cluster to run a container-based service.
cluster_name, service_name = create_ecs_cluster()
sec_app_build_name = create_code_build()
create_code_deploy(cluster_name=cluster_name, service_name=service_name)
create_code_pipeline(sec_app_build_name=sec_app_build_name)
