import asyncio
from tqdm.asyncio import tqdm
from rambler_change.paths import PATH_LIST, PATH_NEW_LIST, PROXY_LIST, PATH_CONFIG, API_FILE
from rambler_change.class_account import AccountManager
from playwright.async_api import async_playwright
from loguru import logger


from rambler_change.logger import set_logger
from rambler_change.scripts import check_and_create_files, read_data, change_password, update_api_key
from rambler_change.scripts import login_rambler, ask_use_proxy, create_context, generate_valid_password, load_config, get_page_cookies


async def main():

    # Инициализация
    config = load_config(PATH_CONFIG)
    api_key = config['API_KEY']
    new_secret_word = config["new_secret_word"]
    update_api_key(api_key, API_FILE)
    set_logger()
    check_and_create_files()

    use_proxy = await ask_use_proxy()
    all_accounts = AccountManager(PATH_LIST, PROXY_LIST, use_proxy)
    async with async_playwright() as playwright:
        data = read_data(PATH_LIST)
        with tqdm(total=len(data), desc="Изменение паролей", unit="пользователь", dynamic_ncols=True, leave=True) as pbar:
            with open(PATH_NEW_LIST, 'a') as new_file:
                for account in all_accounts.accounts:
                    context, page = await create_context(playwright, use_proxy, account.proxy)
                    new_password = generate_valid_password()
                    await login_rambler(account.email, account.password, account.proxy, page)
                    success, cookies_json = await change_password(page, context, account.email, account.password,
                                                                  new_password)
                    with open(PATH_NEW_LIST, 'a') as new_file:
                        if success:
                            # Записываем email, новый пароль и куки JSON в одну строку
                            new_file.write(f"{account.email}:{new_password}:{cookies_json}\n")
                        else:
                            new_file.write(f"{account.email}:{new_password}:WARNING\n")
                            logger.error(f"{account.email}: Не удалось сменить пароль для пользователя")
                    pbar.update(1)


if __name__ == "__main__":
    asyncio.run(main())


