import datetime

def isdate(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        return False
    else:
        return True

def istime(time_text):
    try:
        datetime.datetime.strptime(time_text, '%H:%M')
    except ValueError:
        return False
    else:
        return True

def isfloat(f):
    try:
        ff = float(f)
    except ValueError:
        return False
    else:
        return True

def isEmpty(s):
    return s == "" or s is None