import asyncio
import random
import string
import tempfile
from random import sample
from json.decoder import JSONDecodeError


import httpx
import questionary
import toml
from loguru import logger
from playwright._impl._errors import Error as PlaywrightError
from playwright._impl._errors import TargetClosedError
from playwright.async_api import Playwright, Page, BrowserContext
from playwright.async_api import async_playwright
from rambler_change.paths import JS_DIR
from rambler_change.paths import PATH_LIST, PATH_NEW_LIST, PROXY_LIST
from questionary import Style
from tqdm.asyncio import tqdm

from data.config import CAPTCHA_KEY
from data.config import HEADLESS
from rambler_change.errors import CaptchaTaskCreationError, CaptchaSolutionError, CaptchaError, BadDataAccount, \
    ResponseCodeFailure, AttemptsErrorReached, PageCloseError


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
    length = 20
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


async def check_login_status(login, page) -> bool:
    try:
        await page.locator("//div[@data-cerber-id='profile::avatar::upload_avatar']").wait_for(state='visible',
                                                                                               timeout=20000)
        return True
    except Exception as e:
        return False


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


async def check_captcha_exist(page: Page) -> bool:
    xpath_selector = '//div[@id="anchor"]'
    try:
        await page.wait_for_selector(xpath_selector, timeout=2000)
        return True
    except Exception:
        return False


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


async def change_password(page, account):
    site_key = '322e5e22-3542-4638-b621-fa06db098460'
    url = 'https://id.rambler.ru/account/change-password'

    attempts = 0
    max_attempts = 3

    while attempts < max_attempts:

        try:
            await page.goto('https://id.rambler.ru/account/change-password')
            await page.locator('//*[@id="password"]').fill(account.password)
            await page.locator('//*[@id="newPassword"]').fill(account.new_password)
            logger.info(f'Смена пароля: {account.email} решение капчи...')
            try:
                captcha_result = await solve_captcha_2captcha(CAPTCHA_KEY, site_key, url)
            except CaptchaSolutionError as e:
                logger.error(f"{account.email} ошибка при решении капчи : {e}")
                continue
            await _set_captcha_token(page, captcha_result)
            await page.locator('//button[@data-cerber-id="profile::change_password::save_password_button"]').click()
            await asyncio.sleep(1)
            success = await notification_password_change(page)
            if success:
                await write_data(account.email, account.new_password)
                logger.success(f"{account.email}: Пароль успешно изменён!")
                return
            else:
                logger.warning("Капча не была решена! Перезагружаю страницу и повторяю попытку.")
                await page.reload()
                await asyncio.sleep(2)
                attempts += 1
        except TargetClosedError:
            raise PageCloseError
        except PlaywrightError as exc:
            if 'Timeout' in str(exc):
                logger.error(
                    f'{account.email}: Не смог найти элемент на странице! Попытка: ({attempts}/{max_attempts})!')
                attempts += 1
                continue
        attempts += 1
    await write_bad_data(account.email, account.new_password)
    raise AttemptsErrorReached('Превышено количество попыток смены пароля!')


async def notification_password_change(page: Page) -> bool:
    try:
        await page.wait_for_selector(
            "//div[@class='rui-Snackbar-snackbar rui-Snackbar-center rui-Snackbar-top rui-Snackbar-success rui-Snackbar-isVisible']",
            state="visible", timeout=6000)
        return True
    except Exception as e:
        return False


async def notification_question_change(page: Page) -> bool:
    try:
        await page.wait_for_selector(
            "//div[@class='rui-Snackbar-snackbar rui-Snackbar-center rui-Snackbar-top rui-Snackbar-success rui-Snackbar-isVisible']",
            state="visible", timeout=6000)
        return True
    except Exception as e:
        logger.error(f"Контрольный вопрос не изменён, неизвестная ошибка!")
        return False


def generate_random_word() -> str:
    length: int = 12
    word_length = random.randint(length, length)
    word = ''.join(random.choice(string.ascii_lowercase) for _ in range(word_length))
    return word


async def login_rambler(account, page):

    url = 'https://id.rambler.ru/login-20/login?rname'
    site_key = '322e5e22-3542-4638-b621-fa06db098460'

    attempts = 0
    max_attempts = 3

    while attempts < max_attempts:

        try:
            await page.goto('https://id.rambler.ru/login-20/login?rname')
            await page.locator('//*[@id="login"]').fill(account.email)
            await page.locator('//*[@id="password"]').fill(account.password)
            await page.locator('//button[@type="submit"][@data-cerber-id="login_form::main::login_button"]').click()
            captcha_exist = await check_captcha_exist(page)
            if captcha_exist:
                try:
                    captcha_result = await solve_captcha_2captcha(CAPTCHA_KEY, site_key, url)
                    await _set_captcha_token(page, captcha_result)
                except CaptchaError as e:
                    logger.error(f"{account.email} ошибка при решении капчи : {e}")
                    continue
            await asyncio.sleep(2)
            wrong_log_pass = await check_wrong_log_or_pass(page)
            if wrong_log_pass:
                await write_bad_data(account.email, account.password)
                raise BadDataAccount
            await asyncio.sleep(1)
            ban_status = await check_ban_status(page)
            if ban_status:
                logger.error(f'{account.email}: аккаунт заблокирован!')
            success = await check_login_status(account.email, page)
            if success:
                return
        except TargetClosedError:
            raise PageCloseError
        except PlaywrightError as exc:
            if 'RESPONSE_CODE_FAILURE' in str(exc):
                raise ResponseCodeFailure
            if 'Timeout' in str(exc):
                logger.error(
                    f'{account.email}: Не смог найти элемент на странице! Попытка: ({attempts}/{max_attempts})!')
                attempts += 1
                continue
            raise exc
        attempts += 1
    raise AttemptsErrorReached("Превышено количество попыток логина.")


async def create_context(playwright: Playwright, use_proxy: bool, proxy) -> tuple[BrowserContext, Page]:
    temp_dir = tempfile.mkdtemp()
    try:
        if use_proxy:
            context = await playwright.chromium.launch_persistent_context(
                proxy=proxy.as_playwright_proxy,
                user_data_dir=temp_dir,
                headless=HEADLESS,
            )
            await context.add_init_script(path=JS_DIR)
            page = await context.new_page()
            return context, page
        else:
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=temp_dir,
                headless=HEADLESS,
            )
        await context.add_init_script(path=JS_DIR)
        page = await context.new_page()
        return context, page

    except Exception as e:
        logger.error(f"Ошибка при создании контекста браузера: {str(e)}")
    finally:
        pass


async def solve_captcha_2captcha(api_key: str, site_key: str, url: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
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
        except JSONDecodeError:
            raise CaptchaTaskCreationError(f"Некорректный JSON в ответе")
        except httpx.HTTPError as e:
            raise CaptchaTaskCreationError(f"HTTP ошибка при создании задачи: {e}")
        if response_data.get("status") != 1:
            raise CaptchaTaskCreationError(f"Ошибка при создании задачи: {response_data.get('request')}")

        task_id = response_data["request"]

        while True:
            await asyncio.sleep(5)
            try:
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
            except JSONDecodeError:
                raise CaptchaSolutionError(f"Некорректный JSON в ответе")
            except httpx.HTTPError as e:
                raise CaptchaSolutionError(f"HTTP ошибка при получении результата: {e}")

            if result_data.get("status") == 1:
                return result_data["request"]

            if result_data.get("request") == "CAPCHA_NOT_READY":
                continue
            else:
                raise CaptchaSolutionError(f"ошибка при решении капчи: некорректный JSON в ответе")


async def write_data(login: str, password: str):
    with open(PATH_NEW_LIST, 'a') as new_file:
        new_file.write(f"{login}:{password}\n")


async def write_bad_data(login: str, password: str):
    with open(PATH_NEW_LIST, 'a') as new_file:
        new_file.write(f"{login}:{password}:bad account\n")


async def write_data_question(login: str, password: str, new_question: str):
    try:
        with open(PATH_NEW_LIST, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        lines = []

    updated_lines = []
    found = False
    for line in lines:
        line = line.rstrip('\n')
        if line.startswith(f"{login}:{password}"):
            new_line = f"{login}:{password}:{new_question}\n"
            updated_lines.append(new_line)
            found = True
        else:
            updated_lines.append(line + '\n')
    if not found:
        new_line = f"{login}:{password}:{new_question}\n"
        updated_lines.append(new_line)

    with open(PATH_NEW_LIST, 'w') as file:
        file.writelines(updated_lines)


async def _set_captcha_token(page: Page, captcha_token: str):
    try:
        iframe_element = await page.wait_for_selector('iframe[data-hcaptcha-widget-id]', timeout=10000)
        if not iframe_element:
            raise Exception("Не удалось найти iframe с капчей")

        frame = await iframe_element.content_frame()
        if not frame:
            raise Exception("Не удалось получить контент iframe")

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
    change_password_answer = questionary.select(
        "Менять пароль?",
        choices=["Да", "Нет"],
        style=custom_style
    ).ask()

    if change_password_answer == "Да":
        change_password = True
    else:
        change_password = False

    change_question_answer = questionary.select(
        "Менять контрольный вопрос?",
        choices=["Да", "Нет"],
        style=custom_style
    ).ask()

    if change_question_answer == "Да":
        change_question = True
    else:
        change_question = False

    use_proxy = questionary.select(
        "Использовать прокси?",
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
        "max_tasks": int(max_tasks) if max_tasks else 1,
        "question_answer": change_question,
        "change_password_answer": change_password
    }


async def ask_user_preferences():
    return await asyncio.to_thread(ask_user_preferences_sync)


async def process_account(
        account,
        use_proxy: bool,
        change_question_answer: bool,
        change_password_answer: bool,
        playwright,
        semaphore,
        pbar,
        delay
) -> None:

    await asyncio.sleep(delay)
    async with semaphore:
        context, page = await create_context(playwright, use_proxy, account.proxy)
        try:
            await login_rambler(account, page)
            if change_password_answer:
                await change_password(page, account)
            if change_question_answer:
                await change_question(page, account, change_password_answer)
            pbar.update(1)
        except PageCloseError:
            logger.error(f"{account.email}: Контекст или страница были закрыты: ")
        except ResponseCodeFailure:
            logger.error(f'{account.email}:{account.proxy}: Ошибка подключения, проверьте соединение или прокси!')
        except BadDataAccount:
            logger.error(f'{account.email}: Капча при логине или неправильные данные аккаунта!')
        except AttemptsErrorReached as exc:
            logger.error(f'{account.email}: {exc}')
        finally:
            await context.close()


async def run_change(
        user_response,
        semaphore,
        all_accounts
) -> None:
    async with async_playwright() as playwright:
        data = read_data(PATH_LIST)
        with tqdm(total=len(data), desc="Изменение паролей", unit="пользователь", dynamic_ncols=True,
                  leave=True) as pbar:
            tasks = [
                process_account(
                    account,
                    user_response['proxy'],
                    user_response['question_answer'],
                    user_response['change_password_answer'],
                    playwright,
                    semaphore,
                    pbar,
                    delay=i * 10)
                for i, account in enumerate(all_accounts.accounts)
            ]
            await asyncio.gather(*tasks)


async def change_question(
        page: Page,
        account,
        change_password_answer,
) -> None:
    site_key = '322e5e22-3542-4638-b621-fa06db098460'
    url = 'https://id.rambler.ru/account/change-question'

    attempts = 0
    max_attempts = 3

    while attempts < max_attempts:
        try:
            await page.goto('https://id.rambler.ru/account/change-question')
            await page.locator('//input[@name="answer"]').fill(account.new_question)
            if change_password_answer:
                await page.locator('//input[@id="password"]').fill(account.new_password)
            else:
                await page.locator('//input[@id="password"]').fill(account.password)
            logger.info(f'Смена контрольного вопроса: {account.email} решение капчи...')
            try:
                captcha_result = await solve_captcha_2captcha(CAPTCHA_KEY, site_key, url)
            except CaptchaSolutionError as e:
                logger.error(f"Ошибка при решении капчи!")
                attempts += 1
                continue
            await _set_captcha_token(page, captcha_result)
            await page.locator('//button[@data-cerber-id="profile::change_question::save_question_button"]').click()
            await asyncio.sleep(1)
            success = await notification_password_change(page)
            if success:
                if change_password_answer:
                    await write_data_question(account.email, account.new_password, account.new_question)
                    logger.success(f"{account.email}: контрольный вопрос успешно изменён!")
                else:
                    await write_data_question(account.email, account.password, account.new_question)
                    logger.success(f"{account.email}: контрольный вопрос успешно изменён!")
                return
            else:
                logger.error(f'{account.email}: Ошибка при изменении контрольного вопроса!')
                attempts += 1
                continue
        except TargetClosedError:
            raise PageCloseError
        except PlaywrightError as exc:
            if 'Timeout' in str(exc):
                logger.error(
                    f'{account.email}: Не смог найти элемент на странице! Попытка: ({attempts}/{max_attempts})!')
                attempts += 1
                continue
        attempts += 1
    raise AttemptsErrorReached('Превышено количество попыток смены контрольного вопроса!')
