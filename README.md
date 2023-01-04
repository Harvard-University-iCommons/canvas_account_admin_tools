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


# Self-unenrollment LTI 1.3 Tool

For (ILE) courses that are using self-enrollment, we provide the ability for people to self-unenroll via an LTI 1.3 tool that is installed into the Canvas course site.

This LTI tool provides a link that appears in the right-hand navigation on the course home page.

## LTI 1.3 tool installation

The process for installing an LTI 1.3 tool is a bit different from an LTI 1.1 tool. This project includes some management commands to help facilitate the process.

1. Generate a key pair for the tool using this Django management command:

    ```./manage.py generate_lti_key <key name>```

2. Create a new developer key in Canvas using the tool config url:

    ```https://<tool hostname>/self_unenrollment_tool/config/```

    Copy the client ID that Canvas generates (a long number starting with 1875)

3. Create/update an SSM param with the key `/<env>/canvas_account_admin_tools/self_unenroll_client_id` and the client ID from step 2 as the value.

4. Create a new tool configuration for the tool using this Django management command:

    ```./manage.py create_tool_config --key-name <key name> --host <e.g. canvas.instructure.com> --client-id <1875*******>```

    `<key name>` is the name of the key that was generated in step 1. The hostname is based on the Canvas instance: it should typically be one of: `canvas.instructure.com`, `canvas.test.instructure.com` or `canvas.beta.instructure.com`.

Now the tool is installed in the Canvas instance and is ready to be installed into individual courses.

The self-enrollment management tool will use the client ID to install the LTI tool into a course when self-enrollment is enabled.
