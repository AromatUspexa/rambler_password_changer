import asyncio
from tqdm.asyncio import tqdm
from rambler_change.paths import PATH_LIST, PATH_NEW_LIST, PROXY_LIST, PATH_CONFIG, API_FILE
from rambler_change.class_account import AccountManager
from playwright.async_api import async_playwright
from loguru import logger
from rambler_change.logger import set_logger
from rambler_change.scripts import check_and_create_files, read_data, change_password, update_api_key
from rambler_change.scripts import login_rambler, ask_use_proxy, create_context, generate_valid_password, load_config
<<<<<<< Updated upstream
=======
import aiofiles  # Adding aiofiles for asynchronous file handling


async def process_account(account, playwright, use_proxy, new_secret_word, semaphore):
    async with semaphore:  # Ограничение параллельных задач
        context, page = await create_context(playwright, use_proxy, account.proxy)
        new_password = generate_valid_password()
        await login_rambler(account.email, account.password, account.proxy, page)
        success, cookies_json = await change_password(
            page, context, account.email, account.password, new_password, new_secret_word
        )
        # Записываем результат в файл
        async with aiofiles.open(PATH_NEW_LIST, 'a') as new_file:
            if success:
                await new_file.write(f"{account.email}:{new_password}:{new_secret_word}:{cookies_json}\n")
            else:
                await new_file.write(f"{account.email}:{new_password}:{new_secret_word}:WARNING\n")
                logger.error(f"{account.email}: Не удалось сменить пароль для пользователя")
>>>>>>> Stashed changes


async def main():

    # Инициализация
    config = load_config(PATH_CONFIG)
    api_key = config['API_KEY']
<<<<<<< Updated upstream
=======
    new_secret_word = config["new_secret_word"]
>>>>>>> Stashed changes
    update_api_key(api_key, API_FILE)
    set_logger()
    check_and_create_files()

    use_proxy = await ask_use_proxy()
    all_accounts = AccountManager(PATH_LIST, PROXY_LIST, use_proxy)
<<<<<<< Updated upstream
    async with async_playwright() as playwright:
        data = read_data(PATH_LIST)
        with tqdm(total=len(data), desc="Изменение паролей", unit="пользователь", dynamic_ncols=True, leave=True) as pbar:
            with open(PATH_NEW_LIST, 'a') as new_file:
                for account in all_accounts.accounts:
                    context, page = await create_context(playwright, use_proxy, account.proxy)
                    new_password = generate_valid_password()
                    await login_rambler(account.email, account.password, account.proxy, page)
                    success = await change_password(page, context, account.email, account.password, new_password)
                    if success:
                        with open(PATH_NEW_LIST, 'a') as new_file:
                            new_file.write(f"{account.email}:{new_password}\n")
                    else:
                        with open(PATH_NEW_LIST, 'a') as new_file:
                            new_file.write(f"{account.email}:{new_password}:WARNING\n")
                        logger.error(f"{account.email}: Не удалось сменить пароль для пользователя")
                    pbar.update(1)
=======

    # Ограничение на количество одновременно работающих задач
    semaphore = asyncio.Semaphore(2)  # Например, 5 параллельных задач
    async with async_playwright() as playwright:
        tasks = [
            process_account(account, playwright, use_proxy, new_secret_word, semaphore)
            for account in all_accounts.accounts
        ]

        # Выполнение задач параллельно с прогресс-баром
        with tqdm(total=len(tasks), desc="Изменение паролей", unit="пользователь", dynamic_ncols=True,
                  leave=True) as pbar:
            for f in asyncio.as_completed(tasks):
                await f
                pbar.update(1)

>>>>>>> Stashed changes


if __name__ == "__main__":
    asyncio.run(main())


