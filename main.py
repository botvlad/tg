
Search

Live tail
GMT+3



Collecting blinker>=1.9.0 (from flask->-r requirements.txt (line 2))
  Downloading blinker-1.9.0-py3-none-any.whl.metadata (1.6 kB)
Collecting click>=8.1.3 (from flask->-r requirements.txt (line 2))
  Downloading click-8.3.1-py3-none-any.whl.metadata (2.6 kB)
Collecting itsdangerous>=2.2.0 (from flask->-r requirements.txt (line 2))
  Downloading itsdangerous-2.2.0-py3-none-any.whl.metadata (1.9 kB)
Collecting jinja2>=3.1.2 (from flask->-r requirements.txt (line 2))
  Downloading jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
Collecting markupsafe>=2.1.1 (from flask->-r requirements.txt (line 2))
  Downloading markupsafe-3.0.3-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.7 kB)
Collecting werkzeug>=3.1.0 (from flask->-r requirements.txt (line 2))
  Downloading werkzeug-3.1.4-py3-none-any.whl.metadata (4.0 kB)
Collecting charset_normalizer<4,>=2 (from requests->pyTelegramBotAPI->-r requirements.txt (line 1))
  Downloading charset_normalizer-3.4.4-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (37 kB)
Collecting idna<4,>=2.5 (from requests->pyTelegramBotAPI->-r requirements.txt (line 1))
  Downloading idna-3.11-py3-none-any.whl.metadata (8.4 kB)
Collecting urllib3<3,>=1.21.1 (from requests->pyTelegramBotAPI->-r requirements.txt (line 1))
  Downloading urllib3-2.6.2-py3-none-any.whl.metadata (6.6 kB)
Collecting certifi>=2017.4.17 (from requests->pyTelegramBotAPI->-r requirements.txt (line 1))
  Downloading certifi-2026.1.4-py3-none-any.whl.metadata (2.5 kB)
Downloading pytelegrambotapi-4.29.1-py3-none-any.whl (294 kB)
Downloading flask-3.1.2-py3-none-any.whl (103 kB)
Downloading blinker-1.9.0-py3-none-any.whl (8.5 kB)
Downloading click-8.3.1-py3-none-any.whl (108 kB)
Downloading itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Downloading jinja2-3.1.6-py3-none-any.whl (134 kB)
Downloading markupsafe-3.0.3-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
Downloading werkzeug-3.1.4-py3-none-any.whl (224 kB)
Downloading requests-2.32.5-py3-none-any.whl (64 kB)
Downloading charset_normalizer-3.4.4-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (153 kB)
Downloading idna-3.11-py3-none-any.whl (71 kB)
Downloading urllib3-2.6.2-py3-none-any.whl (131 kB)
Downloading certifi-2026.1.4-py3-none-any.whl (152 kB)
Installing collected packages: urllib3, markupsafe, itsdangerous, idna, click, charset_normalizer, certifi, blinker, werkzeug, requests, jinja2, pyTelegramBotAPI, flask
Successfully installed blinker-1.9.0 certifi-2026.1.4 charset_normalizer-3.4.4 click-8.3.1 flask-3.1.2 idna-3.11 itsdangerous-2.2.0 jinja2-3.1.6 markupsafe-3.0.3 pyTelegramBotAPI-4.29.1 requests-2.32.5 urllib3-2.6.2 werkzeug-3.1.4
[notice] A new release of pip is available: 25.1.1 -> 25.3
[notice] To update, run: pip install --upgrade pip
==> Uploading build...
==> Setting WEB_CONCURRENCY=1 by default, based on available CPUs in the instance
==> Deploying...
==> Uploaded in 14.1s. Compression took 3.4s
==> Build successful 🎉
==> Running 'python main.py'
 * Serving Flask app ''
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:10000
 * Running on http://10.21.178.190:10000
Press CTRL+C to quit
127.0.0.1 - - [04/Jan/2026 18:54:59] "HEAD / HTTP/1.1" 200 -
2026-01-04 18:55:04,440 (__init__.py:1241 MainThread) ERROR - TeleBot: "Threaded polling exception: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running"
2026-01-04 18:55:04,442 (__init__.py:1243 MainThread) ERROR - TeleBot: "Exception traceback:
Traceback (most recent call last):
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 1234, in __threaded_polling
    polling_thread.raise_exceptions()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/util.py", line 115, in raise_exceptions
    raise self.exception_info
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/util.py", line 97, in run
    task(*args, **kwargs)
    ~~~~^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 688, in __retrieve_updates
    updates = self.get_updates(offset=(self.last_update_id + 1),
                               allowed_updates=allowed_updates,
                               timeout=timeout, long_polling_timeout=long_polling_timeout)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 660, in get_updates
    json_updates = apihelper.get_updates(
        self.token, offset=offset, limit=limit, timeout=timeout, allowed_updates=allowed_updates,
        long_polling_timeout=long_polling_timeout)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 339, in get_updates
    return _make_request(token, method_url, params=payload)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 168, in _make_request
    json_result = _check_result(method_name, result)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 197, in _check_result
    raise ApiTelegramException(method_name, result, result_json)
telebot.apihelper.ApiTelegramException: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running
"
==> Your service is live 🎉
==> 
==> ///////////////////////////////////////////////////////////
==> 
==> Available at your primary URL https://tg-glwc.onrender.com
==> 
==> ///////////////////////////////////////////////////////////
2026-01-04 18:55:08,521 (__init__.py:1241 MainThread) ERROR - TeleBot: "Threaded polling exception: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running"
2026-01-04 18:55:08,522 (__init__.py:1243 MainThread) ERROR - TeleBot: "Exception traceback:
Traceback (most recent call last):
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 1234, in __threaded_polling
    polling_thread.raise_exceptions()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/util.py", line 115, in raise_exceptions
    raise self.exception_info
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/util.py", line 97, in run
    task(*args, **kwargs)
    ~~~~^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 688, in __retrieve_updates
    updates = self.get_updates(offset=(self.last_update_id + 1),
                               allowed_updates=allowed_updates,
                               timeout=timeout, long_polling_timeout=long_polling_timeout)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 660, in get_updates
    json_updates = apihelper.get_updates(
        self.token, offset=offset, limit=limit, timeout=timeout, allowed_updates=allowed_updates,
        long_polling_timeout=long_polling_timeout)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 339, in get_updates
    return _make_request(token, method_url, params=payload)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 168, in _make_request
    json_result = _check_result(method_name, result)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 197, in _check_result
    raise ApiTelegramException(method_name, result, result_json)
telebot.apihelper.ApiTelegramException: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running
"
127.0.0.1 - - [04/Jan/2026 18:55:11] "GET / HTTP/1.1" 200 -
2026-01-04 18:55:13,347 (__init__.py:1241 MainThread) ERROR - TeleBot: "Threaded polling exception: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running"
2026-01-04 18:55:13,348 (__init__.py:1243 MainThread) ERROR - TeleBot: "Exception traceback:
Traceback (most recent call last):
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 1234, in __threaded_polling
    polling_thread.raise_exceptions()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/util.py", line 115, in raise_exceptions
    raise self.exception_info
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/util.py", line 97, in run
    task(*args, **kwargs)
    ~~~~^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 688, in __retrieve_updates
    updates = self.get_updates(offset=(self.last_update_id + 1),
                               allowed_updates=allowed_updates,
                               timeout=timeout, long_polling_timeout=long_polling_timeout)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 660, in get_updates
    json_updates = apihelper.get_updates(
        self.token, offset=offset, limit=limit, timeout=timeout, allowed_updates=allowed_updates,
        long_polling_timeout=long_polling_timeout)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 339, in get_updates
    return _make_request(token, method_url, params=payload)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 168, in _make_request
    json_result = _check_result(method_name, result)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 197, in _check_result
    raise ApiTelegramException(method_name, result, result_json)
telebot.apihelper.ApiTelegramException: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running
"
2026-01-04 18:55:19,676 (__init__.py:1241 MainThread) ERROR - TeleBot: "Threaded polling exception: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running"
2026-01-04 18:55:19,677 (__init__.py:1243 MainThread) ERROR - TeleBot: "Exception traceback:
Traceback (most recent call last):
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 1234, in __threaded_polling
    polling_thread.raise_exceptions()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/util.py", line 115, in raise_exceptions
    raise self.exception_info
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/util.py", line 97, in run
    task(*args, **kwargs)
    ~~~~^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 688, in __retrieve_updates
    updates = self.get_updates(offset=(self.last_update_id + 1),
                               allowed_updates=allowed_updates,
                               timeout=timeout, long_polling_timeout=long_polling_timeout)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 660, in get_updates
    json_updates = apihelper.get_updates(
        self.token, offset=offset, limit=limit, timeout=timeout, allowed_updates=allowed_updates,
        long_polling_timeout=long_polling_timeout)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 339, in get_updates
    return _make_request(token, method_url, params=payload)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 168, in _make_request
    json_result = _check_result(method_name, result)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 197, in _check_result
    raise ApiTelegramException(method_name, result, result_json)
telebot.apihelper.ApiTelegramException: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running
"
2026-01-04 18:55:26,007 (__init__.py:1241 MainThread) ERROR - TeleBot: "Threaded polling exception: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running"
2026-01-04 18:55:26,009 (__init__.py:1243 MainThread) ERROR - TeleBot: "Exception traceback:
Traceback (most recent call last):
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 1234, in __threaded_polling
    polling_thread.raise_exceptions()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/util.py", line 115, in raise_exceptions
    raise self.exception_info
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/util.py", line 97, in run
    task(*args, **kwargs)
    ~~~~^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 688, in __retrieve_updates
    updates = self.get_updates(offset=(self.last_update_id + 1),
                               allowed_updates=allowed_updates,
                               timeout=timeout, long_polling_timeout=long_polling_timeout)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 660, in get_updates
    json_updates = apihelper.get_updates(
        self.token, offset=offset, limit=limit, timeout=timeout, allowed_updates=allowed_updates,
        long_polling_timeout=long_polling_timeout)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 339, in get_updates
    return _make_request(token, method_url, params=payload)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 168, in _make_request
    json_result = _check_result(method_name, result)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 197, in _check_result
    raise ApiTelegramException(method_name, result, result_json)
telebot.apihelper.ApiTelegramException: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running
"
2026-01-04 18:55:38,810 (__init__.py:1241 MainThread) ERROR - TeleBot: "Threaded polling exception: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running"
2026-01-04 18:55:38,811 (__init__.py:1243 MainThread) ERROR - TeleBot: "Exception traceback:
Traceback (most recent call last):
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 1234, in __threaded_polling
    polling_thread.raise_exceptions()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/util.py", line 115, in raise_exceptions
    raise self.exception_info
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/util.py", line 97, in run
    task(*args, **kwargs)
    ~~~~^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 688, in __retrieve_updates
    updates = self.get_updates(offset=(self.last_update_id + 1),
                               allowed_updates=allowed_updates,
                               timeout=timeout, long_polling_timeout=long_polling_timeout)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 660, in get_updates
    json_updates = apihelper.get_updates(
        self.token, offset=offset, limit=limit, timeout=timeout, allowed_updates=allowed_updates,
        long_polling_timeout=long_polling_timeout)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 339, in get_updates
    return _make_request(token, method_url, params=payload)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 168, in _make_request
    json_result = _check_result(method_name, result)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 197, in _check_result
    raise ApiTelegramException(method_name, result, result_json)
telebot.apihelper.ApiTelegramException: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running
"
2026-01-04 18:56:03,136 (__init__.py:1241 MainThread) ERROR - TeleBot: "Threaded polling exception: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running"
2026-01-04 18:56:03,138 (__init__.py:1243 MainThread) ERROR - TeleBot: "Exception traceback:
Traceback (most recent call last):
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 1234, in __threaded_polling
    polling_thread.raise_exceptions()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/util.py", line 115, in raise_exceptions
    raise self.exception_info
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/util.py", line 97, in run
    task(*args, **kwargs)
    ~~~~^^^^^^^^^^^^^^^^^
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 688, in __retrieve_updates
    updates = self.get_updates(offset=(self.last_update_id + 1),
                               allowed_updates=allowed_updates,
                               timeout=timeout, long_polling_timeout=long_polling_timeout)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/__init__.py", line 660, in get_updates
    json_updates = apihelper.get_updates(
        self.token, offset=offset, limit=limit, timeout=timeout, allowed_updates=allowed_updates,
        long_polling_timeout=long_polling_timeout)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 339, in get_updates
    return _make_request(token, method_url, params=payload)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 168, in _make_request
    json_result = _check_result(method_name, result)
  File "/opt/render/project/src/.venv/lib/python3.13/site-packages/telebot/apihelper.py", line 197, in _check_result
    raise ApiTelegramException(method_name, result, result_json)
telebot.apihelper.ApiTelegramException: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running
