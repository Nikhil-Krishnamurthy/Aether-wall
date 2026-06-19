import tinytuya

d = tinytuya.BulbDevice(
    dev_id='eb6224cec2a4060340phnr',
    address='192.168.4.221',
    local_key='/dis#|JRO7RZUwh&',
    version='3.3'
)

data = d.status()
print('set_status() result %r' % data)

while True:
    d.turn_on()
    d.turn_off()