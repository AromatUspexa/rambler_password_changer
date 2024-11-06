import asyncio
import tempfile
import toml
import json

from random import sample
from better_proxy import Proxy


import inquirer
from rambler_change.paths import PATH_LIST, PATH_EXTENSION, PATH_NEW_LIST, PROXY_LIST, API_FILE
from playwright.async_api import Playwright, Page, BrowserContext
from inquirer.themes import load_theme_from_dict
from termcolor import colored
from loguru import logger

ALPHNUM = (
        'abcdefghijklmnopqrstuvwxyz' +
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ' +
        '01234567890' +
        '@$!*'
)





def load_config(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        config = toml.load(file)
    return config

def update_api_key(new_api_key: str, file_path: str):
    with open(file_path, 'r', encoding='utf-8') as file:
        settings = json.load(file)

    settings['clientKey'] = new_api_key

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(settings, file, indent=4, ensure_ascii=False)


def check_and_create_files():
    files_to_check = [PATH_NEW_LIST, PATH_LIST, PROXY_LIST]

    for file_path in files_to_check:
        if not file_path.exists():
            file_path.touch()
            print(f"Создан файл: {file_path}")
        else:
            ...


def generate_password(count=1, length=15, chars=ALPHNUM) -> str | list[str]:
    if count == 1:
        return ''.join(sample(chars, length))
    return [''.join(sample(chars, length)) for _ in range(count)]


def read_data(path_list: str) -> list[tuple[str, ...]]:
    with open(path_list, 'r') as file:
        return [tuple(line.strip().split(':')) for line in file]


def is_valid_password(password: str) -> bool:
    return (
            8 <= len(password) <= 32 and
            any(c.isupper() for c in password) and
            any(c.islower() for c in password) and
            any(c.isdigit() for c in password)
    )


def generate_valid_password() -> str:
    while True:
        password = generate_password()
        if is_valid_password(password):
            return password


async def is_frame_exist(page: Page) -> bool:
    img_selector = "//div[@aria-checked='true']"
    try:
        frame_locator = page.frame_locator('iframe[title="Widget containing checkbox for hCaptcha security challenge"]')
<<<<<<< Updated upstream
        await frame_locator.locator(img_selector).wait_for(state='visible', timeout=60000)
=======
        logger.debug("Фрейм РЕШЕННОЙ КАПЧИ hCaptcha найден, проверка элемента капчи по селектору.")

        # Ждем, пока элемент капчи станет видимым
        await frame_locator.locator(img_selector).wait_for(state='visible', timeout=60000)
        logger.debug("ГАЛОЧКА РЕШЕННОЙ КАПЧИ найдена и видна на странице.")

>>>>>>> Stashed changes
        return True
    except Exception as e:
        logger.warning(f"Ошибка при проверке капчи")
        return False


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


async def change_password(page, context, login, password, new_password) -> bool:
    attempts = 0
    max_attempts = 5  # Добавляем максимальное количество попыток
    try:
        while attempts < max_attempts:
<<<<<<< Updated upstream
=======
            # Шаг 1: Нажимаем на "Контрольный вопрос"
           # await page.get_by_label("Контрольный вопрос", exact=True).click()
            await page.locator('//*[@id = "question"]').wait_for(state='visible',timeout=5000)
            await page.locator('//*[@id = "question"]').click()
            await asyncio.sleep(1)

            # Шаг 2: Выбираем "Любимое блюдо" в качестве вопроса
            await page.get_by_text("Любимое блюдо").click()

            # Шаг 3: Вводим секретное слово в ответ на вопрос
            await page.locator('//*[@id="answer"]').fill(new_secret_word)

            # Шаг 4: Вводим текущий пароль
            await page.locator('//*[@id="password"]').fill(password)

            # Шаг 5: Проходим капчу
            captcha_result = await is_frame_exist(page)
            if captcha_result:
                # Шаг 6: Нажимаем "Сохранить" для смены секретного слова
                await page.get_by_role("button", name="Сохранить").click()
                await asyncio.sleep(1)

                # Проверка успешности изменения секретного слова
                secret_success = await notification_secret_change(page)
                if secret_success:
                    logger.success(f'{login}: секретное слово успешно изменено!')
                else:
                    logger.error(f'{login}: ошибка при изменении секретного слова. Повторяю попытку.')
                    await page.reload()
                    await asyncio.sleep(2)
                    attempts += 1
                    continue  # Переход к следующей попытке при неудаче
            else:
                logger.warning("Капча не была решена! Перезагружаю страницу и повторяю попытку.")
                await page.reload()
                await asyncio.sleep(2)
                attempts += 1
                continue

            # Переход к изменению пароля после успешного изменения секретного слова
            await page.locator('//a[@href="/account/change-password"][@class]').wait_for(state='visible',
                                                                                         timeout=60000)
            await page.locator('//a[@href="/account/change-password"][@class]').click()
>>>>>>> Stashed changes
            await page.locator('//*[@id="password"]').fill(password)
            await page.locator('//*[@id="newPassword"]').fill(new_password)
            captcha_result = await is_frame_exist(page)
            if captcha_result:
                await page.locator('//button[@data-cerber-id="profile::change_password::save_password_button"]').click()
                await asyncio.sleep(1)
                # Дополнительная проверка на успешное изменение пароля
                success = await notification_password_change(page)
                if success:
                    logger.success(f'{login}: пароль успешно изменён!')
                    return True  # Успешно завершить цикл и функцию
                else:
                    logger.error(f'{login}: ошибка при изменении пароля. Повторяю попытку.')
                    await page.reload()
                    await asyncio.sleep(2)
            else:
                logger.warning("Капча не была решена! Перезагружаю страницу и повторяю попытку.")
                await page.reload()
                await asyncio.sleep(2)
            attempts += 1  # Увеличиваем счётчик попыток
        logger.error(f"{login}: Превышено количество попыток смены пароля.")
        return False
    finally:
        if context:  # Проверяем, что контекст не был закрыт ранее
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


async def login_rambler(login: str, password: str, proxy: Proxy, page):
    try:
        await page.goto('https://id.rambler.ru/login-20/login?rname')
    except Exception as e:
        if "net::ERR_HTTP_RESPONSE_CODE_FAILURE" in str(e):
            logger.error(f'Ошибка с прокси: {proxy.host} проверьте соеденение.')
    status_login = True
    while status_login:
        await page.locator('//*[@id="login"]').fill(login)
        await page.locator('//*[@id="password"]').fill(password)
        await page.locator('//button[@type="submit"][@data-cerber-id="login_form::main::login_button"]').click()
        exist_captcha = await is_captcha_exist(page)
        if exist_captcha:
            status_login = await solve_captcha(page)
            success = await check_login_errors(login, page)
            if success:
                break
        else:
            success = await check_login_errors(login, page)
            if success:
                break

<<<<<<< Updated upstream
    await page.locator('//a[@href="/account/change-password"][@class]').wait_for(state='visible', timeout=60000)
    await page.locator('//a[@href="/account/change-password"][@class]').click()
=======
            # Заполнение пароля
            logger.debug("Ввод пароля.")
            await page.locator('//*[@id="password"]').fill(password)

            # Нажатие на кнопку входа
            logger.info("Попытка входа нажатием на кнопку 'Войти'.")
            await page.locator('//button[@type="submit"][@data-cerber-id="login_form::main::login_button"]').click()

            # Проверка на наличие капчи
            exist_captcha = await is_captcha_exist(page)
            if exist_captcha:
                logger.debug("Капча обнаружена, запускаем процедуру решения капчи.")
                status_login = await solve_captcha(page)
                success = await check_login_errors(login, page)
                if success:
                    logger.info(f"Успешный вход для пользователя {login} после решения капчи.")
                    break
            else:
                # Проверка на наличие ошибок входа
                success = await check_login_errors(login, page)
                if success:
                    logger.info(f"Успешный вход для пользователя {login} без капчи.")
                    break
        except Exception as e:
            logger.error(f"Ошибка при попытке входа для пользователя {login}: {str(e)}")
            return False  # Выход из функции в случае ошибки при входе

    # Переход на страницу смены секретного слова после успешного входа
    try:
        logger.debug("Переход на страницу смены секретного слова.")
        await page.locator('//a[@href="/account/change-question"][@class]').wait_for(state='visible', timeout=60000)
        await page.locator('//a[@href="/account/change-question"][@class]').click()
        logger.info("Открыта страница смены секретного слова.")
        return True
    except Exception as e:
        logger.error(f"Ошибка при переходе на страницу смены секретного слова: {str(e)}")
        return False
>>>>>>> Stashed changes


async def ask_use_proxy():
    theme = {
        "Question": {
            "brackets_color": "bright_yellow"
        },
        "List": {
            "selection_color": "bright_blue"
        }
    }

    question = [
        inquirer.List(
            "use_proxy",
            message=colored("Использовать ли прокси?", 'light_yellow'),
            choices=['Да', 'Нет'],
        )
    ]

    use_proxy = inquirer.prompt(question, theme=load_theme_from_dict(theme))['use_proxy']

    if use_proxy == 'Да':
        print(colored("Прокси будет использоваться.", 'white'), end='\n\n')
        use_proxy = True
        return True
    else:
        print(colored("Прокси не будет использоваться.", 'white'), end='\n\n')
        use_proxy = False
        return False


async def create_context(playwright: Playwright, use_proxy: bool, proxy) -> tuple[BrowserContext, Page]:
    temp_dir = tempfile.mkdtemp()  # Создаем временную директорию, которая не удалится автоматически
    try:
        if use_proxy:
            context = await playwright.chromium.launch_persistent_context(
                proxy=proxy.as_playwright_proxy,
                user_data_dir=temp_dir,
                headless=False,
                args=[
                    f"--disable-extensions-except={PATH_EXTENSION}",
                    f"--load-extension={PATH_EXTENSION}",
                ],
            )
            page = await context.new_page()
            return context, page
        else:
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=temp_dir,
                headless=False,
                args=[
                    f"--disable-extensions-except={PATH_EXTENSION}",
                    f"--load-extension={PATH_EXTENSION}",
                ],
            )

        page = await context.new_page()
        return context, page  # Возвращаем контекст и страницу для дальнейшего использования

    except Exception as e:
        logger.error(f"Ошибка при создании контекста браузера: {str(e)}")
    finally:
        # Не удаляем временную директорию сразу, т.к. браузер ещё может ею пользоваться
        pass  # Или если нужно уд
