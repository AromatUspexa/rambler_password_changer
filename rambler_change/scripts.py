import questionary
import tempfile
import asyncio
import httpx
import toml

from rambler_change.paths import PATH_LIST, PATH_NEW_LIST, PROXY_LIST
from playwright.async_api import Playwright, Page, BrowserContext
from playwright.async_api import async_playwright
from rambler_change.errors import LoginFailed, BanAccount
from rambler_change.paths import JS_DIR
from data.config import CAPTCHA_KEY
from questionary import Style
from tqdm.asyncio import tqdm
from random import sample
from loguru import logger


def load_config(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        config = toml.load(file)
    return config


def check_and_create_files():
    files_to_check = [PATH_NEW_LIST, PATH_LIST, PROXY_LIST]

    for file_path in files_to_check:
        if not file_path.exists():
            file_path.touch()
            print(f"Создан файл: {file_path}")
        else:
            ...


def generate_password() -> str | list[str]:
    ALPHNUM = (
            'aabbccddeefghijklmnopqrstuvwxyz' +
            'AABBCCDDEEFGHIJKLMNOPQRSTUVWXYZ' +
            '0011223344556677889900' +
            '@'
    )
    count = 1
    length = 15
    chars = ALPHNUM
    if count == 1:
        return ''.join(sample(chars, length))
    return [''.join(sample(chars, length)) for _ in range(count)]


def read_data(path_list: str) -> list[tuple[str, ...]]:
    with open(path_list, 'r') as file:
        return [tuple(line.strip().split(':')) for line in file]


async def is_frame_exist(page: Page) -> bool:
    img_selector = "//div[@aria-checked='true']"
    try:
        frame_locator = page.frame_locator('iframe[title="Widget containing checkbox for hCaptcha security challenge"]')
        await frame_locator.locator(img_selector).wait_for(state='visible', timeout=60000)
        return True
    except Exception as e:
        logger.warning(f"Ошибка при проверке капчи")
        return True


async def check_login_errors(login, page) -> bool:
    try:
        await page.locator("//div[@class='rui-FieldStatus-message']").wait_for(state='visible', timeout=1000)
        logger.error(f'{login}: Ошибка входа! Проверьтье логин или пароль')
        return False
    except Exception as e:
        return True


async def is_captcha_exist(page: Page) -> bool:
    captcha_selector = '//div[@id="anchor"]'
    try:
        frame_locator = page.frame_locator('iframe[title="Widget containing checkbox for hCaptcha security challenge"]')
        await frame_locator.locator(captcha_selector).wait_for(state='visible', timeout=2000)
        return True
    except Exception as e:
        return False


async def check_wrong_log_or_pass(page: Page) -> bool:
    xpath_selector = '//div[@class="rc__bmhVM"]'
    locator = page.locator(xpath_selector)
    return await locator.is_visible()


async def check_ban_status(page: Page) -> bool:
    xpath_selector = "//div[@class='rc__BVnAD rc__E79Z1 styles_text__zlWVh styles_text__1tUs5']"
    locator = page.locator(xpath_selector)
    return await locator.is_visible()


async def solve_captcha(page: Page):
    while True:
        solve_status = await is_frame_exist(page)
        if solve_status:
            logger.info('Нажимаю на кнопку войти')
            await page.locator('//button[@type="submit"][@data-cerber-id="login_form::main::login_button"]').wait_for(
                state='visible', timeout=5000)
            await page.locator('//button[@type="submit"][@data-cerber-id="login_form::main::login_button"]').click()
            return False
        else:
            return True


async def change_password(page, context, account, api_key) -> bool:
    attempts = 0
    max_attempts = 5  # Добавляем максимальное количество попыток
    try:
        while attempts < max_attempts:
            await page.locator('//*[@id="password"]').fill(account.password)
            await page.locator('//*[@id="newPassword"]').fill(account.new_password)
            logger.info(f'{account.email} решение капчи...')
            captcha_result = await solve_captcha_2captcha(api_key)
            await _set_captcha_token(page, captcha_result)
            await page.locator('//button[@data-cerber-id="profile::change_password::save_password_button"]').click()
            await asyncio.sleep(1)
            success = await notification_password_change(page)
            if success:
                return True  # Успешно завершить цикл и функцию
            else:
                logger.warning("Капча не была решена! Перезагружаю страницу и повторяю попытку.")
                await page.reload()
                await asyncio.sleep(2)
            attempts += 1  # Увеличиваем счётчик попыток
        logger.error(f"{account.email}: Превышено количество попыток смены пароля.")
        return False
    finally:
        if context:
            await context.close()


async def notification_password_change(page: Page) -> bool:
    try:
        await page.wait_for_selector(
            "//div[@class='rui-Snackbar-snackbar rui-Snackbar-center rui-Snackbar-top rui-Snackbar-success rui-Snackbar-isVisible']",
            state="visible", timeout=6000)
        return True
    except Exception as e:
        logger.error(f"Пароль не изменён, неизвестная ошибка")
        return False


async def login_rambler(account, page):
    try:
        await page.goto('https://id.rambler.ru/login-20/login?rname')
    except Exception as e:
        if "net::ERR_HTTP_RESPONSE_CODE_FAILURE" in str(e):
            logger.error(f'Ошибка с прокси: {account.proxy} проверьте соеденение.')

    status_login = True
    while status_login:
        await page.locator('//*[@id="login"]').fill(account.email)
        await page.locator('//*[@id="password"]').fill(account.password)
        await page.locator('//button[@type="submit"][@data-cerber-id="login_form::main::login_button"]').click()
        await asyncio.sleep(2)
        wrong_log_pass = await check_wrong_log_or_pass(page)
        if wrong_log_pass:
            logger.error(f'{account.email}: неправильный логин или пароль!')
            raise LoginFailed("Failed to login")
        await asyncio.sleep(1)
        ban_status = await check_ban_status(page)
        if ban_status:
            logger.error(f'{account.email}: аккаунт заблокирован!')
            raise BanAccount("Account is banned")
        exist_captcha = await is_captcha_exist(page)
        if exist_captcha:
            status_login = await solve_captcha(page)
            success = await check_login_errors(account.email, page)
            if success:
                break
        else:
            success = await check_login_errors(account.email, page)
            if success:
                break
    await page.locator('//a[@href="/account/change-password"][@class]').wait_for(state='visible', timeout=60000)
    await page.locator('//a[@href="/account/change-password"][@class]').click()


async def create_context(playwright: Playwright, use_proxy: bool, proxy) -> tuple[BrowserContext, Page]:
    temp_dir = tempfile.mkdtemp()
    try:
        if use_proxy:
            context = await playwright.chromium.launch_persistent_context(
                proxy=proxy.as_playwright_proxy,
                user_data_dir=temp_dir,
                headless=False,
            )
            await context.add_init_script(path=JS_DIR)
            page = await context.new_page()
            return context, page
        else:
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=temp_dir,
                headless=False,
            )
        await context.add_init_script(path=JS_DIR)
        page = await context.new_page()
        return context, page

    except Exception as e:
        logger.error(f"Ошибка при создании контекста браузера: {str(e)}")
    finally:
        pass


async def solve_captcha_2captcha(api_key: str) -> str:
    site_key = '322e5e22-3542-4638-b621-fa06db098460'
    url = 'https://id.rambler.ru/account/change-password'
    async with httpx.AsyncClient() as client:
        create_task_response = await client.post(
            "http://2captcha.com/in.php",
            data={
                "key": api_key,
                "method": "hcaptcha",
                "sitekey": site_key,
                "pageurl": url,
                "json": 1,
            },
        )

        response_data = create_task_response.json()
        if response_data.get("status") != 1:
            raise ValueError(f"Error creating task: {response_data.get('request')}")

        task_id = response_data["request"]

        while True:
            get_result_response = await client.get(
                "http://2captcha.com/res.php",
                params={
                    "key": api_key,
                    "action": "get",
                    "id": task_id,
                    "json": 1,
                },
            )
            result_data = get_result_response.json()
            if result_data.get("status") == 1:
                return result_data["request"]  # Решение капчи

            if result_data.get("request") == "CAPCHA_NOT_READY":
                await asyncio.sleep(5)
            else:
                raise ValueError(f"Error solving captcha: {result_data.get('request')}")


async def _set_captcha_token(page: Page, captcha_token: str):
    try:
        # Ждём появления iframe с капчей
        iframe_element = await page.wait_for_selector('iframe[data-hcaptcha-widget-id]', timeout=10000)
        if not iframe_element:
            raise Exception("Не удалось найти iframe с капчей")

        # Получаем объект Frame для iframe
        frame = await iframe_element.content_frame()
        if not frame:
            raise Exception("Не удалось получить контент iframe")

        # Устанавливаем значение токена в textarea внутри iframe
        await frame.evaluate(
            '''(token) => {
                const textarea = document.querySelector('textarea[name="h-captcha-response"]');
                if (textarea) {
                    textarea.value = token;
                } else {
                    console.error("Не удалось найти textarea внутри iframe");
                }
            }''',
            captcha_token
        )

        # Также устанавливаем значение токена в textarea на основной странице
        await page.evaluate(
            '''(token) => {
                const textarea = document.querySelector('textarea[name="h-captcha-response"]');
                if (textarea) {
                    textarea.value = token;
                } else {
                    console.error("Не удалось найти textarea на странице");
                }
            }''',
            captcha_token
        )

        # Отправляем капчу
        await page.evaluate('hcaptcha.submit()')

    except Exception as e:
        logger.error(f"Ошибка в _set_captcha_token: {e}")
        raise


custom_style = Style([
    ('pointer', 'fg:#ff9800 bold'),
    ('highlighted', 'fg:#ff9800 bold'),
    ('selected', 'fg:#4caf50 bold'),
    ('disabled', 'fg:#bdbdbd italic')
])


def ask_user_preferences_sync():
    use_proxy = questionary.select(
        "Использовать ли прокси?",
        choices=["Да", "Нет"],
        style=custom_style
    ).ask()

    if use_proxy == "Да":
        proxy = True
    else:
        proxy = False

    max_tasks = questionary.text(
        "Введите количество тасков:",
        validate=lambda text: text.isdigit() and int(text) > 0 or "Пожалуйста, введите положительное целое число.",
        style=custom_style
    ).ask()

    return {
        "proxy": proxy,
        "max_tasks": int(max_tasks) if max_tasks else 1
    }


async def ask_user_preferences():
    return await asyncio.to_thread(ask_user_preferences_sync)


async def process_account(account, use_proxy, playwright, semaphore, pbar, delay):
    max_attempts = 3
    attempt = 0

    while attempt < max_attempts:
        try:
            await asyncio.sleep(delay)
            async with semaphore:
                context, page = await create_context(playwright, use_proxy, account.proxy)
                try:
                    await login_rambler(account, page)
                    success = await change_password(page, context, account, CAPTCHA_KEY)
                    if success:
                        with open(PATH_NEW_LIST, 'a') as new_file:
                            new_file.write(f"{account.email}:{account.new_password}\n")
                        logger.success(f"{account.email}: Пароль успешно изменён!")
                        pbar.update(1)
                        return  # Завершаем функцию после успешного выполнения
                    else:
                        with open(PATH_NEW_LIST, 'a') as new_file:
                            new_file.write(f"{account.email}:{account.new_password}:WARNING\n")
                        logger.error(f"{account.email}: Не удалось сменить пароль для пользователя")
                        pbar.update(1)
                        return
                finally:
                    await context.close()  #

        except BanAccount:
            return
        except LoginFailed:
            return
        except Exception as e:
            attempt += 1
            logger.error(f"Ошибка при обработке аккаунта {account.email} (попытка {attempt}/{max_attempts})")
            if attempt < max_attempts:
                logger.info(f"Повторная попытка для аккаунта {account.email}...")
                await context.close()
                await asyncio.sleep(3)
            else:
                logger.error(f"{account.email}: Превышено количество попыток. Пропускаем аккаунт.")
                pbar.update(1)
                return


async def run_change(user_response, semaphore, all_accounts):
    async with async_playwright() as playwright:
        data = read_data(PATH_LIST)
        with tqdm(total=len(data), desc="Изменение паролей", unit="пользователь", dynamic_ncols=True,
                  leave=True) as pbar:
            tasks = [
                process_account(account, user_response['proxy'], playwright, semaphore, pbar, delay=i * 10)
                for i, account in enumerate(all_accounts.accounts)
            ]
            await asyncio.gather(*tasks)


