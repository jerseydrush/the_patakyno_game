[![Version](https://img.shields.io/badge/version-5.1-white.svg)](https://github.com/jerseydrush/the_patakyno_game/releases)

# English:

### The Patakyno Game — point of no return

A Python-based interactive "game" and humorous prank quiz. Answering questions incorrectly progressively alters your Windows appearance and triggers system-level consequences, while completing the quiz restores the original desktop settings captured at launch.

Supported on Windows 10 and Windows 11.

[Download page](https://github.com/jerseydrush/the_patakyno_game/releases)

## ⚠️ Disclaimer: this is NOT a real game!

The app is intended solely for educational and entertainment purposes. A third wrong answer will initiate a **10-second Windows system reboot** (`shutdown /r /t 10`). Use at your own risk.

## Features & Mechanics:

* **Bilingual Support:** Choose between **English** and **Русский** at the start of the game.
* **5-Question Interactive Quiz:** Features custom character images, background visuals, and sound effects (`.wav`).
* **Progressive Consequences for Wrong Answers:**
  * **1st Mistake:** Deducts 1000 Patakyno Credits and changes your desktop wallpaper.
  * **2nd Mistake:** Deducts 1000 Patakyno Credits, switches the application into Deep Dark Red Mode, and forces Windows into Manual accent mode with a deep dark red system color.
  * **3rd Mistake:** Triggers a security alert from Patakyno Intelligence and initiates a **10-second system restart**.
* **Automatic Restoration:** Completing the quiz restores your previous wallpaper, slideshow/solid-color settings, and accent colors captured before the changes were made. Closing the app early leaves the changes in place.

## Setup & Building:

Install dependencies:
```bash
python -m pip install Pillow comtypes pyinstaller
```

Build into a single standalone `.exe`:
```bash
pyinstaller --noconsole --onefile --icon=files/pataka.ico --add-data "files;files" --hidden-import=comtypes patakyno_game_10.py
```

---

# Русский:

### The Patakyno Game — точка невозврата

Интерактивная игра-викторина с юмористическим подтекстом на Python. Неправильные ответы поэтапно меняют оформление Windows и приводят к системным последствиям, а успешное прохождение восстанавливает исходные настройки рабочего стола, сохранённые при запуске.

Поддерживаются Windows 10 и Windows 11.

[Скачать](https://github.com/jerseydrush/the_patakyno_game/releases)

## ⚠️ Предупреждение: это НЕ настоящая игра!

Приложение предназначено исключительно для образовательных и развлекательных целей. Третий неправильный ответ запускает **перезагрузку компьютера через 10 секунд** (`shutdown /r /t 10`). Используйте на свой страх и риск.

## Функционал и механики:

* **Двуязычный интерфейс:** Выбор между **English** и **Русский** на стартовом экране.
* **Викторина из 5 вопросов:** С уникальными иллюстрациями персонажей, фоновым оформлением и звуковыми эффектами (`.wav`).
* **Прогрессивные наказания за ошибки:**
  * **1-я ошибка:** Списание 1000 Patakyno Credits и смена обоев рабочего стола.
  * **2-я ошибка:** Списание 1000 Patakyno Credits, переход окна программы в тёмно-красный режим и принудительное переключение акцентного цвета Windows в ручной тёмно-красный режим.
  * **3-я ошибка:** Предупреждение от Разведки Патакино и запуск **перезагрузки ПК через 10 секунд**.
* **Автоматическое восстановление:** После успешного прохождения всех вопросов исходные обои (включая слайд-шоу или сплошной цвет) и акцентные цвета системы восстанавливаются. При досрочном закрытии игры изменения остаются.

## Установка и сборка:

Установите необходимые библиотеки:
```bash
python -m pip install Pillow comtypes pyinstaller
```

Сборка в один исполняемый `.exe` файл:
```bash
pyinstaller --noconsole --onefile --icon=files/pataka.ico --add-data "files;files" --hidden-import=comtypes patakyno_game_10.py
```