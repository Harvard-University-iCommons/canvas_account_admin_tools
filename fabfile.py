from fabric.api import *
from fabric.contrib.files import exists
env.forward_agent = True
#env.use_ssh_config = True


@task
def deploy_django_project(project_name=None, branch=None, tag=None, deploy_env=None, app_root='/opt'):
    if not project_name:
        abort("Must supply project name (icommons_tools/icommons_lti_tools/icommons_ext_tools/icommons_rest_api)")

    if not deploy_env:
        abort("Must supply the deploy_env (test/qa/production)")

    if not branch and not tag:
        abort("Must supply either a branch or a tag.")

    app_dir = "%s/%s" % (app_root, project_name)

    with cd(app_dir):

        if branch:
            run("git fetch")
            run("git checkout %s" % branch)
            run("git pull")
            
        else:

            # use git describe --tags to find the current tag
            old_tag = run("git describe --tags")

            if tag == old_tag:
                abort("Version %s is already deployed." % tag)
            else:

                print "|%s|" % old_tag

                run("git fetch")
                run("git checkout %s" % tag)

        with prefix("workon %s" % project_name):
            run("pip install -r %s/requirements/%s.txt --upgrade" % (project_name, deploy_env))
            run("python manage.py collectstatic --noinput")

            # make sure that supervisor is running
            supervisor_status = run("python manage.py supervisor status")
            if "refused connection" in supervisor_status:
                run("python manage.py supervisor --noreload --daemonize")

            else:
                run("python manage.py supervisor restart gunicorn")

            '''
            if exists('gunicorn.pid'):
                gunicorn_pid = run("cat gunicorn.pid")
                if gunicorn_pid:
                    run("kill %s; sleep 2; gunicorn -c gunicorn_%s.py %s.wsgi:application" % (gunicorn_pid, deploy_env, project_name))
                else:
                    abort("Couldn't restart gunicorn.")

            else:
                run("gunicorn -c gunicorn_%s.py %s.wsgi:application" % (deploy_env, project_name))
            '''