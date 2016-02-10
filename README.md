# Дристаба
Калофеникс.
## Зависимости
* Python >= 3.4.3
* PostgreSQL >= 9.3
* Redis >= 2.8

## Установка
### Кратко
* Дристаба деплоится как обычное django-приложение. Руководство можно найти на https://docs.djangoproject.com/en/1.9/howto/deployment/ .
* Вебсокет-демон просто запускается с правильно установленной переменной окружения `DJANGO_SETTINGS_MODULE`. Может потребоваться изменение переменной `PYTHONPATH`.

### Пошагово
Рассмотрим типичный сетап комбинации nginx+uwsgi на Ubuntu 14.04.

1. Нам потребуются development-заголовки пистона для сборки модулей, `pip` для установки библиотек и `git`.
   Также нам потребуются Nginx, PostgreSQL и Redis.
  
  ```
  sudo apt-get install python3-dev python3-pip git postgresql-9.3 libpq-dev redis-server nginx-core
  ```

2. Склонируйте репозиторий в удобное для вас место.
  
  ```
  git clone https://github.com/postman0/1chan_django.git
  ```

3. Установите `virtualenv`.

  ```
  pip3 install virtualenv
  ```
  
4. Перейдите в корневую директорию проекта, создайте новое виртуальное окружение и активируйте его.

  ```
  cd 1chan_django
  virtualenv venv -p python3 --prompt \(1chan\)
  . venv/bin/activate
  ```

5. Установите необходимые библиотеки.

  ```
  pip install -r requirements.txt
  ```
  
6. Создайте базу и пользователя в PostgreSQL согласно вашему вкусу. Например,

  ```
  sudo -u postgres createuser -P 1chan
  sudo -u postgres createdb 1chan -E utf8 -O 1chan
  ```
  
7. В корне проекта создайте файл `settings_local.py` и отредактируйте его согласно вашим требованиям. Пример:
  
  ```python
DEBUG = False # обязательно

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '1chan', # имя бд из пункта 6
        'USER': '1chan', # пользователь оттуда же
        'PASSWORD': 'chooh-chooh', # его пароль
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

SECRET_KEY = '' # секретный ключ, просто рандомный текст. Никогда не раскрывайте его посторонним.

MEDIA_ROOT = '/home/jlbyrey/1chan_django/media' # директория для загрузки файлов, абсолютный путь
MEDIA_URL = '/media/' # урл для загруженных файлов

STATIC_ROOT = '/home/jlbyrey/1chan_django/static' # директория для размещения статики. Должна быть отличной от MEDIA_ROOT

ALLOWED_HOSTS = ['prr.pss'] # адреса, под которыми будет доступен сайт. Формат подробно описан в документации Django.

# приватный и публичный ключи рекапчи. Получаются у гуглососаки.
RECAPTCHA_PUBLIC_KEY = '' 
RECAPTCHA_PRIVATE_KEY = ''

# запретить загрузку сайта внутри фреймов
X_FRAME_OPTIONS = 'DENY'

# браузерные костыли от какиров
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# следующие настройки имеют смысл, если ваш калчок доступен по HTTPS
SECURE_HSTS_SECONDS = длительность_в_секундах # длительность HSTS. Заставляет браузеры ходить на сайт только по HTTPS.
SECURE_SSL_REDIRECT = True # авторедирект с HTTP на HTTPS
SESSION_COOKIE_SECURE = True # Выдает сесионные куки только для HTTPS. Вдруг роскомпетух захочет взломать вам админку?
CSRF_COOKIE_SECURE = True
  ```
  
  В [дефолтном файле настроек](https://github.com/postman0/1chan_django/blob/master/onechan_django/settings.py) есть и другие интересные опции, например, `ALLOWED_IMAGE_PATTERNS`. Также там хранятся настройки вебсокет-демона.
  **Не модифицируйте его напрямую**, а задайте нужно значение в `settings_local.py`.
  Полный список настроек Django находится [здесь](https://docs.djangoproject.com/en/1.9/ref/settings/).
  
8. Примените миграции к БД и соберите статику. Опционально можно создать администратора.

  ```
  ./manage.py migrate
  ./manage.py collectstatic
  ./manage.py createsuperuser
  ```
  
9. Установите uwsgi, например:

  ```
  pip install uwsgi
  ```
  
  При установке из pip он собирается из исходников, поэтому это займет немного больше времени, чем обычные пакеты.
  
10. Создайте конфиг uwsgi (например, `1chan.ini`) и отредактируйте его.

  ```ini
[uwsgi]
socket = 127.0.0.1:8000 # адрес, который будет слушать uwsgi
chdir = /абсолютный_путь_до_корня_проекта
virtualenv = /абсолютный_путь_до_корня_проекта/venv/
wsgi-file = onechan_django/wsgi.py
processes = 2 # количество процессов и тредов - по вкусу
threads = 4
harakiri = 30 # убивает запросы, занимающие больше 30 секунд
uid = onechan # под каким пользователем запускать
gid = onechan # под какой группой запускать
daemonize = uwsgi.log # запускает uwsgi на заднем плане и пишет его вывод в uwsgi.log
  ```
  
11. Настройте nginx. Создайте файл `/etc/nginx/sites-enabled/1chan.conf` и отредактируйте его:

  ```nginx
server {

	server_name prr.pss; # адрес вашего калчка

	location / {
		include uwsgi_params;
		uwsgi_pass 127.0.0.1:8000; # здесь адрес uwsgi
	}

  # альтернативно можете попердолиться с директивой alias для статики и медиа
	location /static/ {  # STATIC_URL, если вы его меняли
		root /home/onechan/1chan_django ; # корень проекта
	}

	location /media/ {  # MEDIA_URL из пункта 7
		root /home/onechan/1chan_django ; # корень проекта
	}

	location /ws {
        proxy_pass http://localhost:3000; # WS_LISTEN_ADDRESS, если вы его меняли
        proxy_set_header Host      $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
       	proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
	}

}
  ```
  
12. Заставтьте nginx перечитать конфиг, запустите uwsgi и вебсокет-демон.

  ```sh
  sudo service nginx reload
  uwsgi 1chan.ini
  ./manage.py runws
  # предыдущую строку желательно выполнить в screen или под nohup, если у вас нет менеджера демонов
  ```
  

Калчок готов! :poop:
