import requests
import random
import string
from loguru import logger
import sys

API_URL = 'https://firstmail.ltd/api/v1/email/password/change/'
API_KEY = ''
MAILS_FILE = 'mails.txt'
STATIC_PASSWORD = '1z2x3cZXCSADWQE!'

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    colorize=True,
    level="DEBUG"
)


def generate_password(length=12):
    characters = string.ascii_letters + string.digits
    password_chars = [random.choice(characters) for _ in range(length - 1)]
    password_chars.append('!')
    random.shuffle(password_chars)
    return ''.join(password_chars)


def read_mails_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        mails = []
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            if ':' not in line:
                logger.warning(f"Строка {line_num} имеет неверный формат: {line}")
                continue
            
            parts = line.split(':', 1)
            if len(parts) == 2:
                email, password = parts
                mails.append({'email': email.strip(), 'password': password.strip()})
            else:
                logger.warning(f"Строка {line_num} имеет неверный формат: {line}")
        
        logger.info(f"Загружено {len(mails)} email адресов из {filename}")
        return mails
        
    except FileNotFoundError:
        logger.error(f"Файл {filename} не найден!")
        return []
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {filename}: {e}")
        return []


def change_password(email, current_password, new_password):
    headers = {
        'accept': 'application/json',
        'X-API-KEY': API_KEY,
        'Content-Type': 'application/json',
    }
    
    json_data = {
        'email': email,
        'current_password': current_password,
        'new_password': new_password,
    }
    
    logger.info(f"Отправка запроса для {email}...")
    
    try:
        response = requests.post(API_URL, headers=headers, json=json_data, timeout=30)
        
        if response.status_code == 200:
            logger.success(f"✓ Пароль успешно изменен для {email}")
            logger.info(f"Новый пароль: {new_password}")
            
            try:
                response_json = response.json()
                if response_json:
                    logger.debug(f"Ответ сервера: {response_json}")
            except:
                pass
                
            return True
            
        else:
            logger.error(f"✗ Ошибка для {email} | Статус: {response.status_code}")
            
            try:
                response_json = response.json()
                logger.error(f"Ответ сервера: {response_json}")
            except:
                if response.text:
                    logger.error(f"Ответ сервера: {response.text}")
            
            return False
    
    except requests.exceptions.Timeout:
        logger.error(f"✗ Превышено время ожидания для {email}")
        return False
        
    except requests.exceptions.ConnectionError:
        logger.error(f"✗ Не удалось подключиться к серверу для {email}")
        return False
        
    except Exception as e:
        logger.error(f"✗ Ошибка для {email}: {type(e).__name__} - {str(e)}")
        return False


def save_new_passwords(successful_mails, filename='new_mails.txt'):
    try:
        import os
        
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            with open(filename, 'rb') as f:
                f.seek(-1, 2)
                last_char = f.read(1)
                needs_newline = last_char != b'\n'
        else:
            needs_newline = False
        
        with open(filename, 'a', encoding='utf-8') as f:
            if needs_newline:
                f.write('\n')
            
            for mail_data in successful_mails:
                f.write(f"{mail_data['email']}:{mail_data['new_password']}\n")
        
        logger.success(f"✓ Новые пароли добавлены в {filename}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка при сохранении в {filename}: {e}")
        return False


def main():
    logger.info("=" * 70)
    logger.info("ПРОГРАММА СМЕНЫ ПАРОЛЕЙ")
    logger.info("=" * 70)
    
    mails = read_mails_from_file(MAILS_FILE)
    
    if not mails:
        logger.error("Нет email адресов для обработки. Завершение работы.")
        return
    
    logger.info("-" * 70)
    logger.info("Выберите режим смены пароля:")
    logger.info("1. Статичный пароль (из настроек)")
    logger.info("2. Случайная генерация для каждого email")
    logger.info("-" * 70)
    
    while True:
        choice = input("Ваш выбор (1 или 2): ").strip()
        if choice in ['1', '2']:
            break
        logger.warning("Неверный выбор. Введите 1 или 2.")
    
    use_static = choice == '1'
    
    if use_static:
        logger.info(f"Используется статичный пароль: {STATIC_PASSWORD}")
    else:
        logger.info("Будут сгенерированы случайные пароли для каждого email")
    
    logger.info("-" * 70)
    
    success_count = 0
    failed_count = 0
    successful_mails = []
    
    for idx, mail_data in enumerate(mails, 1):
        email = mail_data['email']
        current_password = mail_data['password']
        
        new_password = STATIC_PASSWORD if use_static else generate_password()
        
        logger.info(f"\n[{idx}/{len(mails)}] Обработка: {email}")
        
        result = change_password(email, current_password, new_password)
        
        if result:
            success_count += 1
            successful_mails.append({
                'email': email,
                'new_password': new_password
            })
        else:
            failed_count += 1
    
    logger.info("-" * 70)
    logger.info("ИТОГОВАЯ СТАТИСТИКА:")
    logger.success(f"✓ Успешно: {success_count}")
    if failed_count > 0:
        logger.error(f"✗ Ошибок: {failed_count}")
    logger.info(f"Всего обработано: {len(mails)}")
    logger.info("=" * 70)
    
    if successful_mails:
        logger.info("")
        save_new_passwords(successful_mails)


if __name__ == "__main__":
    main()
