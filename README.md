# 2FA_SSH
Двухфакторная аутентификация через Telegram Bot на ssh сервер

1. Создаем бота в телеграмме :
Создаем бота через @BotFather. Для чего нужно ввести команду /newbot , далее нужно вести имя и ник бота. В результате нужно получить токен, для доступа к боту.
![image](https://github.com/user-attachments/assets/a3b3ffc5-c371-4a5a-8f08-3a43e7388693)

1.2. Далее необходимо запустить созданного бота через команду /start и что-то в него написать, например, "Привет!"
![image](https://github.com/user-attachments/assets/bece80c3-0963-4505-8fe1-ab0ccea0528c)

1.3. Сообщение нужно для того, чтобы впоследствии узнать ваш Chat ID. Сделать это можно при помощи следующей команды (не забываем указать токен вашего бота):
   
   ```
   curl -s https://api.telegram.org/bot{BOT_TOKEN}/getUpdates | grep -o '"id":[0-9]*' | head -1 | awk -F: '{print $2}'
   ```
Пример того, как это выглядит: 
![image](https://github.com/user-attachments/assets/70aa48ab-47c2-42b6-a350-cffa3a9e22ab)

Для начала, необходимо установить Python, если вдруг его нет.

```
sudo apt update && sudo apt install -y python3 python3-pip
```
И несколько pip пакетов, которые нам пригодятся:
```
pip3 install python-telegram-bot aiofiles requests --break-system-packages
```
Создадим сам python-скрипт , которые реализуют логику двухфакторной аутентификации. В моём примере мы его создаем в этой директроии /opt/2fa_ssh/telegram_auth.py

python-скрипт для копирования тут -  [telegram_auth.py](https://github.com/chichnikita/2FA_SSH/blob/main/telegram_auth.py)

Не забудьте изменить TOKEN и CHAT_ID на ваши.

На линуксе заходим в директорию /etc/pam.d/ и в  ней создаем файл telegram-auth  в который записываем : 
```
auth requisite pam_exec.so stdout /usr/bin/python3 /opt/2fa_ssh/telegram_auth.py
```

В директории /etc/pam.d/ окрываем на редактирование sshd и в конце пишем : 
```
auth include telegram-auth
```

Теперь перезапускаем службу 
```
systemctl restart sshd
```

Готово)
