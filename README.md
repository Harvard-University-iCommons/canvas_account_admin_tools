# Canvas Account Admin Tools

This project provides a collection of tools used to administer courses, users, and other resources in Harvard Academic Technology's instance of Canvas at the sub-account level.


# Releasing

1. **Container Image:** Ensure there is an image in [tlt-nonprod ECR](https://console.aws.amazon.com/ecr/repositories/private/482956169056/uw/canvas-account-admin?region=us-east-1) for the version you want to deploy (e.g. `latest`, commit, branch, tag).

    If the image doesn't already exist, you can kick off a build like so (in tlt-nonprod account):
    ```sh
    aws codebuild start-build --project-name uw-canvas-account-admin-image-build --source-version <git-ref>
    ```

2. **ECS Service:** Deploy the [SSO ECS service stack](https://console.aws.amazon.com/cloudformation/#/stacks?filteringStatus=active&filteringText=uw-canvas-account-admin-tools-ecs-service&viewNested=true&hideStacks=false) with the latest version of [at-cfn-templates/at-generic-django-docker-ecs-service.yaml](https://github.huit.harvard.edu/HUIT/at-cfn-templates/blob/master/at-generic-django-docker-ecs-service.yaml)
    * `ImageTagParameter` should be the version you want to deploy (see Container Image step, above)
    * `WeekdayScheduleParameter` should be `true` for non-prod environments, or `false` (default) for prod
