# rambler_password_changer

[![telegram Channel](https://img.shields.io/badge/telegram-join-%2300A1E4?logo=telegram&logoColor=white&link=https://t.me/ploxo_spal)](https://t.me/ploxo_spal)


Python script for automatic rambler password change


- [Запуск под Windows](#запуск-под-windows)
- [data / config](#Data-/-config)

## Запуск под Windows
- Установите [Python 3.11](https://www.python.org/downloads/windows/). Не забудьте поставить галочку напротив "Add Python to PATH".
- Установите [git](https://git-scm.com/download/win). Это позволит с легкостью получать обновления скрипта командой `git pull`
- Откройте консоль в удобном месте...
  - Склонируйте (или [скачайте](https://github.com/AromatUspexa/rambler_password_changer/archive/refs/heads/main.zip)) этот репозиторий:
    ```bash
    git clone https://github.com/AromatUspexa/rambler_password_changer
    ```
  - Перейдите в папку проекта:
    ```bash
    cd rambler_password_changer
    ```
  - Установите требуемые зависимости следующей командой или запуском файла `INSTALL.bat`:
    ```bash
    pip install -r requirements.txt
    playwright install
    ```
  - Запустите скрипт следующей командой или запуском файла `START.bat`:
    ```bash
    python main.py
    ```

## Data / config

- После зпуска START.bat появится `old_password.txt`, вставьте почты в формате:
    ```bash
    login:password
    login:password
    login:password
    ...
    ```
- В файл `config.toml` вставьте API-key
