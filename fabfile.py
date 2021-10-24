from fabric import Connection, task


conn = Connection('xr@xrboston.org')

@task
def deploy(ctx):
    conn.run('git -C /home/src/extinctionr/ pull')
    conn.run('supervisorctl restart xr')


@task
def backup(ctx):
    with conn.prefix('source /home/xr/venv/bin/activate'):
        conn.run('/home/src/extinctionr/manage.py dumpdata --settings=extinctionr.prod_settings -a -e auth.Permission -e contenttypes.ContentType')
        # conn.run('/home/src/extinctionr/manage.py dumpdata --settings=extinctionr.prod_settings -a -o ~/backup.json')
