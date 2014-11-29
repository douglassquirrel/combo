from time import sleep, time as now

class Alarm:
    def __init__(self, duration):
        if duration is not None:
            self.alarm_time = now() + duration
        else:
            self.alarm_time = None

    def is_ringing(self):
        return self.alarm_time is not None and now() > self.alarm_time

def spin(f, duration):
    alarm = Alarm(duration)
    while True:
        result = f()
        if result is not None:
            return result
        if alarm.is_ringing():
            return None
        sleep(0.1)
