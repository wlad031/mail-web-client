from datetime import datetime


def format_timestamp(timestamp):
    date = datetime.strptime(timestamp, '%a, %d %b %Y %H:%M:%S %Z')
    if (datetime.now() - date).days == 0:
        return date.strftime('Today, %H:%M:%S')
    if (datetime.now() - date).days == 1:
        return date.strftime('Yesterday, %H:%M:%S')
    return date.strftime('%Y-%m-%d %H:%M:%S')
