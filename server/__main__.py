import os
from argparse import ArgumentParser

import uvicorn

from . import db


def register_user_cli():
    username = input("Username: ").strip()
    with db.session() as s:
        if s.query(db.User).filter_by(name=username).first():
            print(f"User {username} already exists")
            return 1
        user = db.User(name=username)
        s.add(user)
        print(f"Created user {user}")


def register_token_cli():
    with db.session() as s:
        users = s.query(db.User).all()
        if not users:
            print("No users exist")
            print("You must create a user first")
            return 1
        for user in users:
            print(user)
        username = input("Username: ").strip()
        user = s.query(db.User).filter_by(name=username).first()
        if not user:
            print(f"User {username} does not exist")
            return 1
        token = db.Token(user=user)
        s.add(token)
        print(token.token())


def list_tokens_cli():
    with db.session() as s:
        for token in s.query(db.Token):
            print(token.token(), token.user.name)


def run():
    uvicorn.run(
        "server.http:app",
        host="0.0.0.0",
        port=8000,
        reload=env == "dev",
        reload_dirs=["server"],
    )


commands = {
    "serve": run,
    "user": register_user_cli,
    "token": register_token_cli,
    "tokens": list_tokens_cli,
    None: run,
}

parser = ArgumentParser()
parser.add_argument(
    "--env", default="dev", help="Environment to run the server in"
)
parser.add_argument(
    "command",
    nargs="?",
    help="Command to run",
    choices=[x for x in commands.keys() if x],
)
args = parser.parse_args()
env = args.env or os.environ.get("ENV", "dev")
command = args.command

print(f"Running in {env} environment")
print(f"Command: {command}")


main = commands.get(command)

if not main:
    print(f"Unknown command {command}")
    exit(1)

exit(main() or 0)
