### Harbor Backend

## Technology:
- Starlette.io
- Gino
- Uvicorn

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
