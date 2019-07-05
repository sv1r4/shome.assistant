
from threading import Thread
import os
import platform
import struct
import sys
import time

class T1(Thread):
    # def __init__():

    def run(self):
        print('hello python thread')
    

if __name__ == '__main__':    
    T1().run()
    print("end")