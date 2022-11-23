import os

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QFileDialog
from PyQt5.QtCore import QTime


WINDOW_SIZE = [350, 170]


alarm_time = ''
fname = ''


class NotSelected(Exception):
    pass


class AlarmWindow(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('alarm_design.ui', self)

        self.setGeometry(500, 300, *WINDOW_SIZE)
        self.setWindowTitle('Укажите время')

        self.select.clicked.connect(self.select_track)
        self.set_alarm.clicked.connect(self.setting)

        self.selected = False

    def select_track(self):
        global fname

        fname = QFileDialog.getOpenFileName(
            self, 'Выбрать мелодию', '', '(*.mp3)')[0]

        self.selected = True

        self.name = os.path.basename(fname)
        n = 0

        # достаём только название песни (без расширения)
        for i in self.name[::-1]:
            n += 1
            if i == '.':
                self.name = self.name[:-n]
                break

        self.alarm_track_name.setText(self.name)

    def setting(self):
        global alarm_time

        try:
            if not self.selected:
                raise NotSelected

            self.hour = self.spin_hour.value()
            self.minute = self.spin_minute.value()
            self.second = self.spin_second.value()

            alarm_time = QTime(
                self.hour, self.minute, self.second, 0).toString('hh:mm:ss')

            self.close()

        except NotSelected:
            self.alarm_track_name.setText('Сначала выберите мелодию.')
