import asyncio
from data.config import CAPTCHA_KEY

from rambler_change.paths import PATH_LIST, PROXY_LIST, PATH_CONFIG
from rambler_change.scripts import check_and_create_files
from rambler_change.class_account import AccountManager
from rambler_change.scripts import ask_user_preferences
from rambler_change.scripts import run_change
from rambler_change.logger import set_logger
from rambler_change.author import TG_LINK


async def main():

    set_logger()

    print(f"telegram channel: {TG_LINK}")

    check_and_create_files()
    if not CAPTCHA_KEY:
        print(f"Вставьте 2captcha ключ в: {PATH_CONFIG}")
        return

    user_response = await ask_user_preferences()
    all_accounts = AccountManager(PATH_LIST, PROXY_LIST, user_response['proxy'])
    max_concurrent_tasks = user_response['max_tasks']
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    await run_change(user_response, semaphore, all_accounts)


if __name__ == "__main__":
    asyncio.run(main())
