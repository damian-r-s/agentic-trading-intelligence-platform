"""Admin-only user creation. Run with: python -m scripts.create_user"""
import getpass

from src.core.security import hash_password
from src.core.databases.repositories.users_repo import create_user, get_user_by_username


def main() -> None:
    username = input("Username: ").strip()
    if get_user_by_username(username) is not None:
        print(f"User '{username}' already exists.")
        return

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords don't match.")
        return

    user_id = create_user(username, hash_password(password))
    print(f"Created user '{username}' (id={user_id}).")


if __name__ == "__main__":
    main()
