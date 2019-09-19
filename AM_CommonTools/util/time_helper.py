import time

#===========================================
#   Class to group certqain functions that
#   are related to time stamps
#
# By: Kenny Davila
#     Rochester Institute of Technology
#     2013
#===========================================
class TimeHelper:
    def __init__(self):
        self.start_time = 0
        self.end_time = 0
        self.total_elapsed = 0.0
        self.started = False


    def reset(self):
        self.start_time = 0
        self.end_time = 0
        self.total_elapsed = 0.0
        self.started = False

    def startTimer(self):
        self.start_time = time.time()
        self.started = True

    def endTimer(self):
        if self.started:
            self.end_time = time.time()
            self.total_elapsed += (self.end_time - self.start_time)
            self.started = False

    def lastElapsedTime(self):
        return self.end_time - self.start_time

    def totalElapsedTime(self):
        return self.total_elapsed

    def lastElapsedStamp(self):
        return TimeHelper.secondsToStr(self.lastElapsedTime())

    def totalElapsedStamp(self):
        return TimeHelper.secondsToStr(self.total_elapsed)

    #========================================================
    #  Converts a milliseconds time into a string time
    #  stamp
    #========================================================
    @staticmethod
    def stampToStr(milliseconds):
        #....milliseconds in one hour...
        hours = int(milliseconds / 3600000.0)
        milliseconds %= 3600000.0

        #....milliseconds in one minute...
        minutes = int(milliseconds / 60000.0)
        milliseconds %= 60000.0

        seconds = milliseconds / 1000.0

        h = ("0" if hours < 10 else "") + str(hours)
        m = ("0" if minutes < 10 else "") + str(minutes)

        rem = seconds - int(seconds)
        seconds = int(seconds)
        s = ("0" if seconds < 10 else "") + str(seconds)
        dot = str(rem)[2:4]
        while len(dot) < 2:
            dot += "0"

        return h + ":" + m + ":" + s + "." + dot

    #========================================================
    # Seconds to string
    #========================================================
    @staticmethod
    def secondsToStr(seconds):
        return TimeHelper.stampToStr(seconds * 1000)


