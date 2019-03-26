### Harbor Backend

## Technology:
- Starlette.io
- Gino
- Uvicorn

## Instructions for setting up locally:
Download gino, uvicorn, and postgresql <br/>
Pull from harbor-backend repo

Do following commands to change postgres user password:
1. `sudo -i -u postgres`
2. enter password

Now you should be in the postgres command prompt. Follow below:
1. `createdb {DB_NAME}``
1. `psql`

You should now be at the postgres=# prompt. Follow below:
1. `ALTER USER postgres with password {some password}``
2. `\q`

(If you think that didn't work, then consider doing next:)
Within the postgres=# prompt:
1. `\password`
2. Enter password and confirm again
3. `\q`

Now we must edit the harbor.env file. You must only edit the password (and the
DB_NAME field if you changed the table name).

Now in the regular terminal:
1. `python harbor.py`
<br/><br/>
:)

## Deployment Instruction (the same is true for frontend/just different pem/ip):
- `sudo chmod 400 harbor-frontend-pem.txt`
- `ssh -i harbor-frontend.pem.txt ubuntu@{IP_ADDRESS}`
- `tmux` or `tmux attach-session -t {id_of_session}`
- `git pull origin master` just in case you want to get updated code
- `npm run build`
- `serve -s build`
- `Ctrl+b` release `d`
- `Ctrl+C` for killing the server on tmux session
- Super good resource: https://linuxize.com/post/getting-started-with-tmux/
