import os


class Config:
    GROUP_NAME = 'ubank'
    PROJECT_NAME = 'cleaner_pdf'
    
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    SAVE_DIR = '/storage/mydatacenter/' + PROJECT_NAME + '/'
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    FILE_DIR = os.path.join(SAVE_DIR, 'data')
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(FILE_DIR, exist_ok=True)

    TIMEZONE = 'Asia/Shanghai'
    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'

    SCHEDULED_DICT = {
        'time_interval': int(os.getenv('TIME_INTERVAL', 720)),       # 每12小时
    }

    HOST_LOCAL = '192.168.3.110'
    HOST_REMOTE = '192.168.3.110'

    MONGO_DICT = {
        'host': HOST_LOCAL,
        'port': 27017,
        'db': GROUP_NAME,
        'username': 'root',
        'password': '123456',
    }


