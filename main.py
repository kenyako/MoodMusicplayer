# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
import time
from random import choice, randint
from PyQt5 import QtMultimedia
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PIL import Image

from equalizer_bar import EqualizerBar
import alarm_window
import radio


MAIN_WINDOW_SIZE = [722, 584]
PLAYER_BTN_SIZE = [25, 25]


class MoodMusicPlayer(QMainWindow):
    def __init__(self):

        super().__init__()
        uic.loadUi("design.ui", self)
        self.initUi()

        self.current_track_name = ""

    def initUi(self):

        self.setGeometry(470, 250, *MAIN_WINDOW_SIZE)
        self.setWindowTitle("Mood Music player")
        self.setWindowIcon(QIcon("images/icons/vinyl_icon.png"))

        # добавление иконок на кнопки плеера
        self.play_btn.setIcon(QIcon("images/icons/play.png"))
        self.play_btn.setIconSize(QSize(*PLAYER_BTN_SIZE))

        self.pause_btn.setIcon(QIcon("images/icons/pause.png"))
        self.pause_btn.setIconSize(QSize(*PLAYER_BTN_SIZE))

        self.stop_btn.setIcon(QIcon("images/icons/stop.png"))
        self.stop_btn.setIconSize(QSize(*PLAYER_BTN_SIZE))

        self.previous_btn.setIcon(QIcon("images/icons/previous.png"))
        self.previous_btn.setIconSize(QSize(*PLAYER_BTN_SIZE))

        self.next_btn.setIcon(QIcon("images/icons/next.png"))
        self.next_btn.setIconSize(QSize(*PLAYER_BTN_SIZE))
        # -----------------------------------

        # эквалайзер
        self.equalizer = EqualizerBar(
            5,
            [
                "#063000",
                "#0A4E00",
                "#0D6500",
                "#118300",
                "#159F00",
                "#19BF00",
                "#1EE400",
                "#22FF00",
                "#87FF75",
                "#B9FFAE",
                "#D8FFD4",
            ],
        )

        self.eq_layout.addWidget(self.equalizer)

        self._timer = QTimer()
        self._timer.setInterval(100)
        self._timer.timeout.connect(self.update_values)
        # -----------------------------------

        # часы и дата
        self.clock.setFrameShape(QFrame.NoFrame)
        self.clock.setSmallDecimalPoint(False)
        self.clock.setDigitCount(8)
        self.clock.setSegmentStyle(QLCDNumber.Flat)
        self.clock.display(QTime.currentTime().toString("hh:mm:ss"))
        time_slot = QTimer(self)
        time_slot.start(1000)

        self.date.setSmallDecimalPoint(False)
        self.date.setSegmentStyle(QLCDNumber.Flat)
        self.date.setDigitCount(10)
        self.date.display(QDate.currentDate().toString("dd.MM.yyyy"))

        time_slot.timeout.connect(self.update_clock)
        # -----------------------------

        # открытие окна с установкой будильника
        self.alarm_btn.triggered.connect(self.open_alarm)
        # -------------------------------------

        # формирование плейлиста
        self.data_for_list = []

        self.list_mood = []
        self.list_genre = []

        for btn in self.moods_btns.buttons():
            btn.clicked.connect(self.create_playlist)
            self.list_mood.append(btn)

        for btn in self.genres_btns.buttons():
            btn.clicked.connect(self.create_playlist)
            self.list_genre.append(btn)
        # -------------------------------------

        # функции плеера
        self.playlist.itemClicked.connect(self.player_funcs)
        self.play_btn.clicked.connect(self.playMusic)
        self.pause_btn.clicked.connect(self.pauseMusic)
        self.stop_btn.clicked.connect(self.stopMusic)
        # переключение между песнями
        self.previous_btn.clicked.connect(self.previous_song)
        self.next_btn.clicked.connect(self.next_song)
        # -------------------------------------

        # Изменение громкости
        self.volume_slider.valueChanged.connect(self.change_volume)
        # -------------------------------------

        # счётчик времени песни
        self.music_timer.setDigitCount(4)
        self.music_timer.setSmallDecimalPoint(True)
        self.cnt_min = 0
        self.cnt_sec = 0
        self.music_timer.display(
            QTime(0, self.cnt_min, self.cnt_sec, 0).toString("m:ss")
        )

        self.timer_mus = QTimer(self)
        self.timer_mus.start(1000)
        self.timer_mus.timeout.connect(self.update_timer)

        self.min_song = 0
        self.sec_song = 0

        self.playing = False
        # -------------------------------------

        # реализация радио
        my_file = open("radio_channels.txt", encoding="UTF-8")

        for i in my_file:
            separator = i.split("|")
            name_radio = separator[0]

            self.radio_list.addItem(name_radio)
            radio.channels.append(i)

        self.start_radio.clicked.connect(self.play_music_radio)
        self.stop_radio.clicked.connect(self.stop_music_radio)
        # ---------------------------------------

        # установка заднего фона
        self.background_set.triggered.connect(self.setting_back)
        # ---------------------------------------

    def player_funcs(self):
        self.db = sqlite3.connect("database\music.sqlite")
        self.cur = self.db.cursor()

        self.current_song = self.playlist.currentItem().text()

        self.load_music(
            self.cur.execute(
                """SELECT path FROM playlist
                            WHERE track_name=?""",
                (self.current_song,),
            ).fetchone()[0]
        )

        self.db.close()

    def playMusic(self):
        # проверка на то, включено ли радио
        if radio.flag == 1:
            radio.flag = 0
            time.sleep(1)

        if self.current_track_name != self.current_song:
            self.cnt_min = 0
            self.cnt_sec = 0
            self.music_timer.display(QTime(0, 0, 0, 0).toString("m:ss"))

        self.player.play()
        self._timer.start()

        self.duration = self.player.duration()

        self.current_track_name = self.playlist.currentItem().text()

        self.min_song = self.duration // 1000 // 60
        self.sec_song = self.duration // 1000 % 60

        self.playing = True

    def pauseMusic(self):
        self.player.pause()
        self._timer.stop()

    def stopMusic(self):
        self.player.stop()
        self._timer.stop()

        self.playing = False
        self.cnt_min = 0
        self.cnt_sec = 0
        self.music_timer.display(
            QTime(0, self.cnt_min, self.cnt_sec, 0).toString("m:ss")
        )

    # переключить на песню назад
    def previous_song(self):
        self.current_row = self.playlist.currentRow() - 1

        if self.playlist.currentRow() == 0:
            self.playlist.setCurrentRow(24)
            self.current_song = self.playlist.currentItem().text()

        else:
            self.playlist.setCurrentRow(self.current_row)
            self.current_song = self.playlist.currentItem().text()

        self.db = sqlite3.connect("database\music.sqlite")
        self.cur = self.db.cursor()

        self.load_music(
            self.cur.execute(
                """SELECT path FROM playlist
                        WHERE track_name=?""",
                (self.current_song,),
            ).fetchone()[0]
        )

        self.db.close()

        self.playMusic()

    # ---------------------------------------------

    # переключить на песню вперёд
    def next_song(self):
        self.current_row = self.playlist.currentRow() + 1

        if self.playlist.currentRow() == 24:
            self.playlist.setCurrentRow(0)
            self.current_song = self.playlist.currentItem().text()

        else:
            self.playlist.setCurrentRow(self.current_row)
            self.current_song = self.playlist.currentItem().text()

        self.db = sqlite3.connect("database\music.sqlite")
        self.cur = self.db.cursor()

        self.load_music(
            self.cur.execute(
                """SELECT path FROM playlist
                        WHERE track_name=?""",
                (self.current_song,),
            ).fetchone()[0]
        )

        self.db.close()

        self.playMusic()

    # ---------------------------------------------

    def load_music(self, filename):
        media = QUrl.fromLocalFile(filename)
        content = QtMultimedia.QMediaContent(media)
        self.player = QtMultimedia.QMediaPlayer()
        self.player.setMedia(content)
        self.player.setVolume(self.volume_slider.value())

    def update_timer(self):
        if self.playing:
            if self.player.state() == QtMultimedia.QMediaPlayer.PausedState:
                if self.current_track_name != self.current_song:
                    self.playing = False
                    self.cnt_min = 0
                    self.cnt_sec = 0
                    self.music_timer.display(
                        QTime(0, self.cnt_min, self.cnt_sec, 0).toString("m:ss")
                    )

            # условие, которое выполняется, если песня перелистывается автоматически
            elif self.duration == 0:
                self.duration = self.player.duration()
                self.min_song = self.duration // 1000 // 60
                self.sec_song = self.duration // 1000 % 60
                self.cnt_sec += 1
                self.music_timer.display(
                    QTime(0, self.cnt_min, self.cnt_sec, 0).toString("m:ss")
                )

            elif self.current_track_name != self.current_song:
                self.playing = False
                self._timer.stop()
                self.cnt_min = 0
                self.cnt_sec = 0
                self.music_timer.display(
                    QTime(0, self.cnt_min, self.cnt_sec, 0).toString("m:ss")
                )

            elif self.cnt_sec == self.sec_song and self.cnt_min == self.min_song:
                self.next_song()

            else:
                self.cnt_sec += 1

                if self.cnt_sec > 59:
                    self.cnt_min += 1
                    self.cnt_sec = 0

                self.music_timer.display(
                    QTime(0, self.cnt_min, self.cnt_sec, 0).toString("m:ss")
                )

    def change_volume(self, value):
        if self.playing:
            self.player.setVolume(value)

    # радио-методы
    def play_music_radio(self):
        radio.flag = 0
        time.sleep(1)

        name_radio = self.radio_list.currentItem().text()

        if self.playing:
            self.stopMusic()

            for i in radio.channels:
                if name_radio in i:
                    separator = i.split("|")
                    channel = separator[1].strip()

                    radio.radioplay(channel)

        else:
            for i in radio.channels:
                if name_radio in i:
                    separator = i.split("|")
                    channel = separator[1].strip()

                    radio.radioplay(channel)

    def stop_music_radio(self):
        radio.flag = 0
        time.sleep(1)

    def closeEvent(self, event):
        # остановка потока при событии закрытии программы
        self.stop_music_radio()

        event.accept()

    # --------------------------------------------------

    def create_playlist(self):
        self.playlist.clear()
        self.data_for_list.clear()
        current_button = self.sender().text()

        # приведение кнопок к общему виду
        for btn in self.moods_btns.buttons():
            btn.setStyleSheet(
                """QPushButton{color: #22FF00;background-color: #052200;}
            QPushButton:hover{border: 1px solid #22FF00;background-color: #072800;}
            QPushButton:pressed{color: black;background-color: #22FF00;}"""
            )

        for btn in self.genres_btns.buttons():
            btn.setStyleSheet(
                """QPushButton{color: #22FF00;background-color: #052200;}
            QPushButton:hover{border: 1px solid #22FF00;background-color: #072800;}
            QPushButton:pressed{color: black;background-color: #22FF00;}"""
            )
        # ----------------------------------

        # обозначение выбранного плейлиста
        QApplication.instance().sender().setStyleSheet(
            """QPushButton{color: black;background-color: #22FF00;}"""
        )
        # ----------------------------------

        db = sqlite3.connect("database\music.sqlite")
        cur = db.cursor()

        if QApplication.instance().sender() in self.list_mood:
            result = cur.execute(
                """SELECT track_name FROM playlist
                    WHERE mood=(SELECT id FROM moods
                    WHERE title=?)""",
                (current_button,),
            ).fetchall()

        if QApplication.instance().sender() in self.list_genre:
            result = cur.execute(
                """SELECT track_name FROM playlist
                    WHERE genre=(SELECT id FROM genres
                    WHERE title=?)""",
                (current_button,),
            ).fetchall()

        db.close()

        for _ in range(25):
            song = choice(result)[0]

            while song in self.data_for_list:
                song = choice(result)[0]

            self.data_for_list.append(song)

        for i in self.data_for_list:
            self.playlist.addItem(i)

    def open_alarm(self):
        self.alarm = alarm_window.AlarmWindow()
        self.alarm.show()

    def update_clock(self):

        time_format = QTime.currentTime()
        time_format = time_format.toString("hh:mm:ss")

        self.clock.display(time_format)
        self.date.display(QDate.currentDate().toString("dd.MM.yyyy"))

        if alarm_window.alarm_time == time_format:

            media_2 = QUrl.fromLocalFile(alarm_window.fname)
            content_2 = QtMultimedia.QMediaContent(media_2)
            self.player_alarm = QtMultimedia.QMediaPlayer()
            self.player_alarm.setMedia(content_2)

            self.player_alarm.play()

            if self.playing:
                self.pauseMusic()

            message = QMessageBox.information(
                self, "Сообщение", "Сработал будильник!", QMessageBox.Ok
            )

            if message == QMessageBox.Ok:
                self.player_alarm.stop()

                if self.playing:
                    self.playMusic()

    # обновление эквалайзера
    def update_values(self):
        self.equalizer.setValues(
            [
                min(100, v + randint(0, 50) if randint(0, 5) > 2 else v)
                for v in self.equalizer.values()
            ]
        )

    def setting_back(self):
        self.back_image = QFileDialog.getOpenFileName(
            self, "Выбрать картинку", "")[0]

        self.pixmap = QPixmap(self.back_image)

        if (
            self.pixmap.width() < 721
            or self.pixmap.width() > 800
            and self.pixmap.height() < 561
            or self.pixmap.height() > 600
        ):
            message = QMessageBox.warning(
                self,
                "Сообщение",
                "Минимальная ширина и высота изображения: 721; 561\
                Максимальная ширина и высота изображения: 800; 600",
            )
        else:
            self.background.setPixmap(self.pixmap)

            image = Image.open(self.back_image)
            im_rgba = image.copy()
            im_rgba.putalpha(90)
            im_rgba.save("new.png")

            self.pixmap = QPixmap("new.png")
            self.background.setPixmap(self.pixmap)

            os.remove("new.png")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(
        """
        QMessageBox QLabel{color: #22FF00;} 
        QMessageBox QPushButton{color: #22FF00; background-color: #149200;} 
        QMessageBox QPushButton:hover{border: 1px solid #22FF00; background-color: #072800;}"""
    )
    ex = MoodMusicPlayer()
    ex.show()
    sys.exit(app.exec())
