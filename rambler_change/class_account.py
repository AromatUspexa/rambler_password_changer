from better_proxy import Proxy
from rambler_change.scripts import generate_password


class Account:
    def __init__(self, email: str, password: str, proxy: Proxy, new_password: str):
        self.email = email
        self.password = password
        self.proxy = proxy
        self.new_password = new_password

    def __str__(self):
        return f"Account(email={self.email}, proxy={self.proxy})"


class AccountManager:
    def __init__(self, account_file: str, proxy_file: str = None, use_proxy: bool = True):
        self.accounts = self._load_accounts(account_file, proxy_file, use_proxy)

    def _load_accounts(self, account_file: str, proxy_file: str = None, use_proxy: bool = True) -> list[Account]:
        global proxies_data
        accounts_data = self._load_file(account_file)

        if use_proxy:
            # Проверяем наличие proxy_file, если выбран режим с прокси
            if proxy_file is None:
                raise ValueError("Не указан файл с прокси, хотя выбран режим использования прокси.")

            proxies_data = self._load_file(proxy_file)

            if len(accounts_data) != len(proxies_data):
                raise ValueError("Количество аккаунтов и прокси должно совпадать.")

        accounts = []
        for index, account_line in enumerate(accounts_data):
            new_password = generate_password()
            email, password = account_line.strip().split(':')
            # Если прокси не используются, передаем None
            if use_proxy:
                proxy = Proxy.from_str(proxies_data[index].strip())
            else:
                proxy = None
            accounts.append(Account(email, password, proxy, new_password))
        return accounts

    def _load_file(self, file_path: str) -> list[str]:
        with open(file_path, 'r') as file:
            return file.readlines()

