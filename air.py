import os, serial, time, json, datetime, struct

JSON_FILE = 'data.json'
CMD_QUERY_DATA = 4

ser = serial.Serial()
ser.port = "/dev/ttyUSB1"
ser.baudrate = 9600

ser.open()
ser.flushInput()


def getPMS():
    ser.write(construct_command(CMD_QUERY_DATA))
    d = read_response()
    values = []
    if d[1] == "\xc0":
        values = process_data(d)
    return values


def construct_command(cmd, data=[]):
    assert len(data) <= 12
    data += [0, ] * (12 - len(data))
    checksum = (sum(data) + cmd - 2) % 256
    ret = "\xaa\xb4" + chr(cmd)
    ret += ''.join(chr(x) for x in data)
    ret += "\xff\xff" + chr(checksum) + "\xab"

    return ret


def read_response():
    byte = 0
    while byte != "\xaa":
        byte = ser.read(size=1)

    d = ser.read(size=9)

    return byte + d


def process_data(d):
    r = struct.unpack('<HHxxBB', d[2:])
    pm25 = r[0] / 10.0
    pm10 = r[1] / 10.0
    checksum = sum(ord(v) for v in d[2:8]) % 256
    return [pm25, pm10]


def writeToJSONFile(datetime, pms):
    try:
        with open(JSON_FILE) as json_data:
            data = json.load(json_data)
    except IOError as e:
        data = []

    jsonrow = {'pm25': pms[0], 'pm10': pms[1], 'datetime': datetime}
    data.append(jsonrow)

    with open(JSON_FILE, 'w') as json_file:
        json.dump(data, json_file, sort_keys=True)


def getDateTime():
    todayDatetime = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return todayDatetime


def writeAndSleep():
    while True:
        writeToJSONFile(getDateTime(), getPMS())
        time.sleep(3600)


def createJSON():
    data = []
    with open(JSON_FILE, 'w') as json_file:
        json.dump(data, json_file)


if os.path.isfile(JSON_FILE):
    print('file found')
    writeAndSleep()
else:
    print('file not found')
    createJSON()
    writeAndSleep()
