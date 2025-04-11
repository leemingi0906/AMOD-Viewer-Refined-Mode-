#
# armaviewer.py
# arma-rs-utils
#
# Created by Junggyun Oh on 04/04/2023.
# Copyright (c) 2023 Junggyun Oh, Yechan Kim All rights reserved.
#
import glob
import os
import os.path as pth
import random as rd
import sys
from datetime import datetime
import warnings

import cv2
import imageio
import matplotlib.image as mpimg
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd
import qimage2ndarray as q2n
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QRadioButton, QGroupBox, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QCheckBox, QButtonGroup, QInputDialog, QSizePolicy, QLineEdit, QFileDialog, QMessageBox)

import multiviewset as MVS
import util

warnings.filterwarnings("ignore", category=DeprecationWarning)

class ArmaViewer(QWidget):
    def __init__(self):
        super().__init__(flags=Qt.Window)
        self.supported_classes = (
            'Armored', 'Artillery', 'Boat', 'Helicopter', 'LCU', 'MLRS', 'Plane', 'RADAR', 'SAM',
            'Self-propelled Artillery', 'Support', 'TEL', 'Tank'
        )
        self.initialize_var_let_widget()
        self.init_levels()
        self.make_levels()
        self.init_ui()

    def initialize_var_let_widget(self):

        def init_ui_settings_constants():
            self.remark_limit = 30
            self.side_space, self.updown_space = 15, 10

        def init_global_constants():
            self.key_map = {
                Qt.Key_A: self.goto_prev_scene,
                Qt.Key_D: self.goto_next_scene,
                Qt.Key_W: self.goto_prev_view,
                Qt.Key_S: self.goto_next_view,
            }
            self.FIXED_COLOR_STYLE = {
                'Armored': [(244,67,54), '-'],
                'Armored:APC': [(244,67,54), '-'],
                'Armored:ASV': [(239,62,49), '--'],
                'Armored:IFV': [(234,57,44), '-.'],
                'Armored:MRAP': [(229,52,39), ':'],
                'Artillery': [(255,51,204), '-'],
                'Boat': [(156,39,176), '-'],
                'Boat:Boat': [(156,39,176), '-'],
                'Boat:RHIB': [(151,34,171), '--'],
                'Helicopter': [(103,58,183), '-'],
                'Helicopter:AH': [(103,58,183), '-'],
                'Helicopter:CH': [(98,53,178), '--'],
                'Helicopter:OH': [(93,48,173), '-.'],
                'Helicopter:UH': [(88,43,168), ':'],
                'LCU': [(63,81,181), '-'],
                'MLRS': [(33,150,243), '-'],
                'Plane': [(0,188,212), '-'],
                'Plane:Attacker': [(0,188,212), '-'],
                'Plane:Bomber': [(0,183,207), '--'],
                'Plane:Cargo': [(0,178,202), '-.'],
                'Plane:Fighter': [(0,173,197), ':'],
                'RADAR': [(0,150,136), '-'],
                'SAM': [(76,175,80), '-'],
                'Self-propelled Artillery': [(139,195,74), '-'],
                'Support': [(205,220,57), '-'],
                'Support:Mil_car': [(205,220,57), '-'],
                'Support:Mil_truck': [(200,215,52), '--'],
                'Support:ASV':[(195,210,47), '-.'],
                'Tank': [(255,122,0), '-'],
                'TEL': [(121,85,72), '-'],
            }
            self.dsize = (640, 480)

        def init_global_variables():
            self.anno_file = ''
            self.checked_list = []
            self.auto_plot_timer = QTimer()
            self.auto_plot_index = 0

        def init_lvl0_panel_widget():
            self.image_widget = QLabel(self)
            self.image_pixmap = QPixmap('figs/AMOD-Viewer-Logo.png')

            target_height = 130
            target_width = int(self.image_pixmap.width() * (target_height / self.image_pixmap.height()))
            self.image_pixmap = self.image_pixmap.scaled(target_width, target_height)
            # print(self.image_pixmap.width(), self.image_pixmap.height())

            self.image_widget.setPixmap(self.image_pixmap)
            self.image_widget.setFixedSize(self.image_pixmap.size())

        def init_lvl1_panel_widget():
            self.set_input = QLineEdit(self, placeholderText='Set Path - ex) /home/user/Downloads/altis_sunny_6_20')
            self.set_select_btn, self.open_csv_btn, self.open_meta_btn, self.open_image_btn = \
                (QPushButton(i, self) for i in ('Open', 'Open Annotation', 'Meta CSV', 'Image'))

        def lvl1_panel_widget_setting():
            btns = (self.set_input, self.set_select_btn, self.open_csv_btn, self.open_meta_btn, self.open_image_btn)
            sizes = (600, 100, 125, 81, 57)
            [btn.setFixedWidth(width) for btn, width in zip(btns, sizes)]

            self.set_select_btn.clicked.connect(self.db_parse)
            self.open_csv_btn.clicked.connect(lambda: util.open_file(self.ds.get_eo_annotation_path() if self.eo_radio.isChecked() else self.ds.get_ir_annotation_path()))
            self.open_meta_btn.clicked.connect(lambda: util.open_file(self.ds.get_set_metacsv_path() if self.eo_radio.isChecked() else self.ds.get_set_metacsv_path()))
            self.open_image_btn.clicked.connect(lambda: util.open_file(self.ds.get_eo_path() if self.eo_radio.isChecked() else self.ds.get_ir_path()))

        def init_lvl2_panel_widget():
            self.num_of_scene_lbl = QLabel(f'{"|" * 7} W {"|" * 8}')
            self.goto_input = QLineEdit(self, placeholderText='#')
            self.goto_scene_btn = QPushButton('Go', self)
            self.prev_scn, self.first_scn, self.next_scn, self.prev_vue, self.base_vue, self.next_vue = \
                (QPushButton(i, self) for i in ('<<<', '#1', '>>>', '-', '0', '+'))

        def lvl2_panel_widget_setting():
            btns = (self.goto_input, self.goto_scene_btn, self.prev_scn, self.first_scn, self.next_scn)
            sizes = (80, 30, 40, 29, 40)
            [btn.setFixedWidth(width) for btn, width in zip(btns, sizes)]
            [btn.setFixedWidth(30) for btn in (self.prev_vue, self.base_vue, self.next_vue)]

            [btn.clicked.connect(func) for func, btn in
             zip((self.goto_prev_scene, self.goto_first_scene, self.goto_next_scene),
                 (self.prev_scn, self.first_scn, self.next_scn))]
            [btn.clicked.connect(func) for func, btn in
             zip((self.goto_prev_view, self.goto_base_view, self.goto_next_view),
                 (self.prev_vue, self.base_vue, self.next_vue))]
            self.goto_scene_btn.clicked.connect(self.goto_scene)

        def init_lvl3_panel_widget():
            title = ('Random Shuffle', 'Sort', 'Remark Sort')
            self.file_num_name = QLabel(f'{"|" * 5} A  S  D {"|" * 5}')
            self.pix_w_input, self.pix_h_input = QLineEdit(self, placeholderText='640'), QLineEdit(self, placeholderText='480')
            self.pix_x = QLabel(' ✕ ')
            self.set_pix_size = QPushButton('Set', self)
            self.img_mix, self.img_sort, self.rmk_sort = (QPushButton(i, self) for i in title)

        def lvl3_panel_widget_setting():
            [btn.setFixedWidth(width) for btn, width in
             zip((self.img_mix, self.img_sort, self.rmk_sort), (125, 43, 95))]

            self.pix_w_input.setFixedWidth(60)
            self.pix_h_input.setFixedWidth(60)
            self.set_pix_size.setFixedWidth(40)
            self.set_pix_size.clicked.connect(self.change_res)
            self.img_mix.clicked.connect(lambda: rd.shuffle(self.ds.get_scene_path_list()))
            self.img_sort.clicked.connect(lambda: self.ds.get_scene_path_list().sort())
            self.rmk_sort.clicked.connect(self.remark_sort)

        def init_lvl4_panel_widget():
            self.use_group = QButtonGroup()
            title = ('Option', 'Usable', 'Label', 'Animate')
            self.option_btngroup, self.usable_btngroup, self.label_btngroup, self.animate_btngroup = (QGroupBox(i) for i in title)
            self.option_box, self.usable_box, self.label_box, self.animate_box = (QHBoxLayout() for _ in range(4))

            self.eo_radio, self.ir_radio, self.eo_and_ir_radio, self.eo_plus_ir_radio = (QRadioButton(i) for i in ('EO', 'IR', 'EO/IR', 'EO+IR'))
            self.t_check, self.f_check = (QCheckBox(i) for i in ('True', 'False'))
            title = ('Center Point', 'Oriented BBOX', 'BBox', 'Main', 'Middle', 'ID')
            self.center_check, self.obox_check, self.bbox_check, self.main_check, self.mid_check, self.id_check = \
                (QCheckBox(i) for i in title)
            self.static_radio, self.auto_radio = (QRadioButton(i) for i in ('Static', 'Dynamic'))

        def lvl4_panel_widget_setting():
            self.option_btngroup.setLayout(self.option_box)

            self.eo_radio.clicked.connect(self.plot_eo)
            self.ir_radio.clicked.connect(self.plot_ir)
            self.eo_and_ir_radio.clicked.connect(self.plot_eo_and_ir)
            self.eo_plus_ir_radio.clicked.connect(self.plot_eo_plus_ir)


            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 여기 점검할 것 :) !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # path = self.ds.get_view_path()
            # _, eo_result = enumerate(self.is_eo_valid(path))
            # _, ir_result = enumerate(self.is_ir_valid(path))
            # self.disable_option_btn(eo_result, ir_result)

            self.use_group.setExclusive(False)
            self.usable_btngroup.setLayout(self.usable_box)
            self.t_check.setChecked(True)
            for idx, btn in enumerate([self.t_check, self.f_check]):
                self.use_group.addButton(btn, idx)
                self.usable_box.addWidget(btn, alignment=Qt.AlignLeading)
            self.use_group.buttonClicked[int].connect(self.change_image_at_view)

            self.label_btngroup.setLayout(self.label_box)
            for i in [self.center_check, self.obox_check, self.bbox_check, self.main_check, self.mid_check,
                      self.id_check]:
                self.label_box.addWidget(i, alignment=Qt.AlignCenter)
                i.toggled.connect(self.checkbox_toggle)
                i.toggled.connect(lambda: self.plot_eo() if self.eo_radio.isChecked() else self.plot_ir() if self.ir_radio.isChecked() else self.plot_eo_and_ir() if self.eo_and_ir_radio.isChecked() else self.plot_eo_plus_ir() if self.eo_plus_ir_radio.isChecked() else None)
                i.toggled.connect(self.create_legend)

            self.animate_btngroup.setLayout(self.animate_box)
            self.animate_box.addWidget(self.static_radio, alignment=Qt.AlignCenter)
            self.animate_box.addWidget(self.auto_radio, alignment=Qt.AlignCenter)

            self.static_radio.setChecked(True)
            self.static_radio.clicked.connect(lambda: self.auto_plot_timer.stop())
            self.auto_plot_timer.timeout.connect(self.auto_plot_step)
            self.auto_radio.clicked.connect(self.auto_plot)

        def init_lvl5_panel_widget():
            self.pixmap, self.lbl_img = QPixmap(), QLabel()
            self.view_group = QButtonGroup()
            self.lgd_layout, self.view_layout = QVBoxLayout(), QVBoxLayout()
            self.lgd_box, self.view_box = QGroupBox('Legend'), QGroupBox('View')

        def lvl5_panel_widget_setting():
            self.lgd_box.setFixedWidth(167)
            self.lgd_box.setFixedHeight(200)
            self.view_box.setFixedWidth(167)
            self.view_box.setFixedHeight(250)
            self.view_group.setExclusive(True)

        def init_lvl6_panel_widget():
            title = ('PNG', 'SVG', 'PDF', 'GIF', 'Report Issue', 'Hello Out There')
            self.png_save, self.svg_save, self.pdf_save, self.gif_save, self.report, self.extra = \
                (QPushButton(i, self) for i in title)
            self.indicator = QLabel(f'{"|" * 45}')

        def lvl6_panel_widget_setting():
            [btn.setFixedWidth(50) for btn in (self.png_save, self.svg_save, self.pdf_save, self.gif_save)]
            self.png_save.clicked.connect(self.save_png)
            self.svg_save.clicked.connect(lambda: self.save_plot('svg'))
            self.pdf_save.clicked.connect(lambda: self.save_plot('pdf'))
            self.gif_save.clicked.connect(self.save_gif)
            self.report.clicked.connect(self.create_report_dialog)
            self.extra.clicked.connect(util.create_extra_dialog)

        init_ui_settings_constants()
        init_global_constants()
        init_global_variables()

        init_lvl0_panel_widget()
        init_lvl1_panel_widget()
        init_lvl2_panel_widget()
        init_lvl3_panel_widget()
        init_lvl4_panel_widget()
        init_lvl5_panel_widget()
        init_lvl6_panel_widget()

        lvl1_panel_widget_setting()
        lvl2_panel_widget_setting()
        lvl3_panel_widget_setting()
        lvl4_panel_widget_setting()
        lvl5_panel_widget_setting()
        lvl6_panel_widget_setting()

    def init_levels(self):
        self.lvl0, self.lvl1, self.lvl2, self.lvl3, self.lvl4, self.lvl5, self.lvl6 = (QHBoxLayout() for _ in range(7))

    def make_levels(self):
        self.lvl0.addSpacing(self.side_space)
        self.lvl0.addWidget(self.image_widget, alignment=Qt.AlignCenter)
        self.lvl0.addSpacing(self.side_space)

        self.lvl1.addSpacing(self.side_space)
        self.lvl1.addWidget(self.set_input, alignment=Qt.AlignCenter)
        self.lvl1.addWidget(self.set_select_btn, alignment=Qt.AlignCenter)
        self.lvl1.addStretch(1)
        self.lvl1.addWidget(self.open_csv_btn, alignment=Qt.AlignCenter)
        self.lvl1.addWidget(self.open_meta_btn, alignment=Qt.AlignCenter)
        self.lvl1.addWidget(self.open_image_btn, alignment=Qt.AlignCenter)
        self.lvl1.addSpacing(self.side_space)

        self.lvl2.addSpacing(self.side_space)
        self.lvl2.addWidget(self.num_of_scene_lbl, alignment=Qt.AlignCenter)
        self.lvl2.addStretch(1)
        self.lvl2.addWidget(self.goto_input, alignment=Qt.AlignCenter)
        self.lvl2.addWidget(self.goto_scene_btn, alignment=Qt.AlignCenter)
        self.lvl2.addSpacing(5)
        self.lvl2.addWidget(self.prev_scn, alignment=Qt.AlignCenter)
        self.lvl2.addWidget(self.first_scn, alignment=Qt.AlignCenter)
        self.lvl2.addWidget(self.next_scn, alignment=Qt.AlignCenter)
        self.lvl2.addSpacing(5)
        self.lvl2.addWidget(self.prev_vue, alignment=Qt.AlignCenter)
        self.lvl2.addWidget(self.base_vue, alignment=Qt.AlignCenter)
        self.lvl2.addWidget(self.next_vue, alignment=Qt.AlignCenter)
        self.lvl2.addSpacing(self.side_space)

        self.lvl3.addSpacing(self.side_space)
        self.lvl3.addWidget(self.file_num_name, alignment=Qt.AlignCenter)
        self.lvl3.addStretch(1)
        self.lvl3.addWidget(self.pix_w_input, alignment=Qt.AlignCenter)
        self.lvl3.addWidget(self.pix_x, alignment=Qt.AlignCenter)
        self.lvl3.addWidget(self.pix_h_input, alignment=Qt.AlignCenter)
        self.lvl3.addWidget(self.set_pix_size, alignment=Qt.AlignCenter)

        self.lvl3.addWidget(self.img_mix, alignment=Qt.AlignCenter)
        self.lvl3.addWidget(self.img_sort, alignment=Qt.AlignCenter)
        self.lvl3.addWidget(self.rmk_sort, alignment=Qt.AlignCenter)
        self.lvl3.addSpacing(self.side_space)

        self.lvl4.addSpacing(self.side_space)
        self.lvl4.addWidget(self.option_btngroup, alignment=Qt.AlignCenter)
        self.lvl4.addStretch(1)
        self.lvl4.addWidget(self.usable_btngroup, alignment=Qt.AlignCenter)
        self.lvl4.addStretch(1)
        self.lvl4.addWidget(self.label_btngroup, alignment=Qt.AlignCenter)
        self.lvl4.addStretch(1)
        self.lvl4.addWidget(self.animate_btngroup, alignment=Qt.AlignCenter)
        self.lvl4.addSpacing(self.side_space)

        extra_box = QVBoxLayout()
        extra_box.addWidget(self.lgd_box, alignment=Qt.AlignTop)
        extra_box.addStretch(1)
        extra_box.addWidget(self.view_box, alignment=Qt.AlignTop)

        self.lvl5.addStretch(1)
        self.lvl5.addWidget(self.lbl_img, alignment=Qt.AlignCenter)
        self.lvl5.addStretch(1)
        self.lvl5.addLayout(extra_box)
        self.lvl5.addSpacing(self.side_space)

        self.lvl6.addSpacing(self.side_space)
        self.lvl6.addWidget(self.png_save, alignment=Qt.AlignCenter)
        self.lvl6.addWidget(self.svg_save, alignment=Qt.AlignCenter)
        self.lvl6.addWidget(self.pdf_save, alignment=Qt.AlignCenter)
        self.lvl6.addWidget(self.gif_save, alignment=Qt.AlignCenter)
        self.lvl6.addStretch(1)
        self.lvl6.addWidget(self.indicator, alignment=Qt.AlignCenter)
        self.lvl6.addStretch(1)
        self.lvl6.addWidget(self.report, alignment=Qt.AlignCenter)
        self.lvl6.addWidget(self.extra, alignment=Qt.AlignCenter)
        self.lvl6.addSpacing(self.side_space)

    def init_ui(self):
        vbox = QVBoxLayout()
        vbox.addSpacing(self.updown_space)
        [vbox.addLayout(i) for i in (self.lvl0, self.lvl1, self.lvl2, self.lvl3, self.lvl4, self.lvl5, self.lvl6)]
        vbox.addSpacing(self.updown_space)

        self.setLayout(vbox)
        self.setWindowTitle('AMOD-Viewer')
        self.resize(1020, 865)
        util.move_to_center(self)
        self.show()

    def db_parse(self):
        input_path = self.set_input.text().replace('file:///', '').replace('"', '').strip()
        input_path1 = os.path.join(input_path, sorted(os.listdir(input_path))[0])
        input_path2 = os.path.join(input_path1, os.listdir(input_path1)[0])
        input_path3 = os.listdir(input_path2)

        is_eo = True if [True for i in input_path3 if 'EO' in i] else False
        is_ir = True if [True for i in input_path3 if 'IR' in i] else False
        is_eo_and_ir = is_eo and is_ir

        if is_eo_and_ir:
            self.option_box.addWidget(self.eo_radio, alignment=Qt.AlignCenter)
            self.option_box.addWidget(self.ir_radio, alignment=Qt.AlignCenter)
            self.option_box.addWidget(self.eo_and_ir_radio, alignment=Qt.AlignCenter)
            self.option_box.addWidget(self.eo_plus_ir_radio, alignment=Qt.AlignCenter)
            self.eo_and_ir_radio.setChecked(True)
        elif is_eo:
            self.option_box.addWidget(self.eo_radio, alignment=Qt.AlignCenter)
            self.eo_radio.setChecked(True)
        elif is_ir:
            self.option_box.addWidget(self.ir_radio, alignment=Qt.AlignCenter)
            self.ir_radio.setChecked(True)

        try:
            self.ds = MVS.MultiViewSet()
            self.ds.set_path_and_name(input_path)
            self.ds.update_best_view_idx()
            self.num_of_scene_lbl.setText(f'# of Scenes : {util.count_legit_folder(self.ds.get_set_path())}')
            self.change_image_at_scene()
        except:
            return

    def change_image_at_scene(self):
        self.checkbox_toggle()
        self.change_image_info()
        self.create_legend()
        self.create_multiview()
        self.change_image_at_view()
        self.change_indicator()

    def change_res(self):
        self.dsize = (int(self.pix_w_input.text()), int(self.pix_h_input.text()))
        self.change_image_at_scene()

    def checkbox_toggle(self):
        self.checked_list = \
            [i for i, btn in enumerate(
                (self.center_check, self.obox_check, self.bbox_check, self.main_check, self.mid_check, self.id_check)
            ) if btn.isChecked()]

    def change_image_info(self):
        idx, name = self.ds.get_scene_index(), self.ds.get_scene_name()
        try:
            metacsv_file = self.ds.get_metacsv()
            row = metacsv_file[metacsv_file['i_time'] == name]
            remark = row.remarks.values[0] if not pd.isna(row.remarks.values[0]) else '-'
            remark = remark if len(remark) < self.remark_limit else remark[:self.remark_limit] + '...'
            self.file_num_name.setText(
                f'#{idx + 1} | Scene Name : {name}'
                f'  ==  {row.hour.values[0]} : {str(row.minute.values[0]).zfill(2)}'
                f' / {row.weather.values[0].title()} / {remark}')
        except ValueError:
            self.file_num_name.setText(f'#{idx + 1} | Scene Name : {name}')

    def create_legend(self):
        for i in reversed(range(self.lgd_layout.count())):
            widget = self.lgd_layout.itemAt(i).widget()
            if widget:
                self.lgd_layout.removeWidget(widget)
                widget.deleteLater()

        if self.eo_radio.isChecked() or self.eo_plus_ir_radio.isChecked() or self.eo_and_ir_radio.isChecked():
            self.anno_file = self.ds.get_eo_csv()
        else:
            self.anno_file = self.ds.get_ir_csv()

        self.anno_file = self.filter_non_supported_classes(self.anno_file)

        lbllbl = set([f'{r["main_class"]}:{r["middle_class"]}' for _, r in self.anno_file.iterrows()])

        dupl_check = set()
        for i in lbllbl:
            label_text = ''
            main_class, middle_class = i.split(':')
            if 4 not in self.checked_list:
                if main_class in dupl_check: continue
                dupl_check.add(main_class)
                label_text = f'<span style="color: rgb{self.FIXED_COLOR_STYLE[main_class][0]};">◆</span> {main_class}'
            elif all(x in self.checked_list for x in [3, 4]):
                rl = main_class if main_class == middle_class else i
                label_text = f'<span style="color: rgb{self.FIXED_COLOR_STYLE[rl][0]};">◆</span> {rl}'
            elif 3 not in self.checked_list and 4 in self.checked_list:
                rl = main_class if main_class == middle_class else i
                label_text = f'<span style="color: rgb{self.FIXED_COLOR_STYLE[rl][0]};">◆</span> {middle_class}'
            self.lgd_layout.addWidget(QLabel(label_text))
        self.lgd_box.setLayout(self.lgd_layout)

    def create_multiview(self):
        for i in reversed(range(self.view_layout.count())):
            widget = self.view_layout.itemAt(i).widget()
            if widget:
                self.view_layout.removeWidget(widget)
                widget.deleteLater()

        self.view_box.setLayout(self.view_layout)
        self.angle = sorted(list(map(int, os.listdir(self.ds.get_scene_path()))))

        for idx, i in enumerate(self.angle):
            lbl = QRadioButton(str(i))
            self.view_layout.addWidget(lbl)
            self.view_group.addButton(lbl, idx)
        self.view_group.buttonClicked[int].connect(self.goto_view)

    def change_image_at_view(self):
        self.plot_eo() if self.eo_radio.isChecked() else self.plot_ir() if self.ir_radio.isChecked() else self.plot_eo_and_ir() if self.eo_and_ir_radio.isChecked() else self.plot_eo_plus_ir()
        clicked_angle_id = self.angle.index(int(self.ds.get_view_name()))
        self.view_group.button(clicked_angle_id).setChecked(True)
        self.view_box.setTitle(f'View : {self.ds.get_view_name()}')

    def change_indicator(self):
        idx = self.ds.get_scene_index() + 1
        length = len(self.ds.get_scene_path_list())
        self.indicator.setText(f'{"|" * int(((idx / length) * 45))}')

    def plot_eo(self):
        # path = self.ds.get_view_path()
        # print(path)
        # print(self.is_eo_valid(path))
        # eo_result, _ = enumerate(self.is_eo_valid(path))
        # print(eo_result)
        # ir_result, _ = enumerate(self.is_ir_valid(path))
        # print(ir_result)
        # self.not_found_warning(eo_result, ir_result)

        """Plot the image with different annotations based on the selected options."""
        canvas = cv2.imread(self.ds.get_eo_path())
        canvas = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        canvas = self.plot_canvas(canvas)
        canvas = cv2.resize(canvas, dsize=self.dsize, interpolation=cv2.INTER_CUBIC)
        self.set_scale_and_policy(canvas)

    def plot_ir(self):
        canvas = cv2.imread(self.ds.get_ir_path())
        canvas = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        canvas = self.plot_canvas(canvas)
        canvas = cv2.resize(canvas, dsize=self.dsize, interpolation=cv2.INTER_CUBIC)
        self.set_scale_and_policy(canvas)

    def plot_eo_and_ir(self):
        eo_image = cv2.imread(self.ds.get_eo_path())
        eo_image = cv2.cvtColor(eo_image, cv2.COLOR_BGR2RGB)
        eo_image = self.plot_canvas(eo_image)
        eo_image = cv2.resize(eo_image, dsize=self.dsize, interpolation=cv2.INTER_CUBIC)

        try:
            ir_image = cv2.imread(self.ds.get_ir_path())
            ir_image = cv2.cvtColor(ir_image, cv2.COLOR_BGR2RGB)
            ir_image = self.plot_canvas(ir_image)
            ir_image = cv2.resize(ir_image, dsize=self.dsize, interpolation=cv2.INTER_CUBIC)
            eo_and_ir_image = cv2.hconcat([eo_image, ir_image])
            self.set_scale_and_policy(eo_and_ir_image)
        except:
            self.eo_radio.setChecked(True)
            self.set_scale_and_policy(eo_image)

    def plot_eo_plus_ir(self):
        eo_image = cv2.imread(self.ds.get_eo_path())
        eo_image = cv2.cvtColor(eo_image, cv2.COLOR_BGR2RGB)

        ir_image = cv2.imread(self.ds.get_ir_path())
        ir_image = cv2.cvtColor(ir_image, cv2.COLOR_BGR2RGB)

        eo_plus_ir_image = cv2.addWeighted(eo_image, 0.5, ir_image, 0.5, 0)

        canvas = self.plot_canvas(eo_plus_ir_image)
        canvas = cv2.resize(canvas, dsize=self.dsize, interpolation=cv2.INTER_CUBIC)
        self.set_scale_and_policy(canvas)

    def plot_canvas(self, canvas, folder_path=None):

        def get_label_and_color(main_class_, middle_class_):
            if 4 not in self.checked_list:
                return main_class_, self.FIXED_COLOR_STYLE[main_class_][0]
            label_ = main_class_ if main_class_ == middle_class_ else f'{main_class_}:{middle_class_}'
            return label_, self.FIXED_COLOR_STYLE[label_][0]

        thickness = 2 * round(canvas.shape[1] / 640)

        if folder_path is None:
            if self.eo_radio.isChecked() or self.eo_plus_ir_radio.isChecked():
                self.anno_file = self.ds.get_eo_csv()
            else:
                self.anno_file = self.ds.get_ir_csv()
        else:
            csv_files = glob.glob(os.path.join(folder_path, '*.csv'))[0]
            self.anno_file = pd.read_csv(csv_files)

        self.anno_file = self.filter_non_supported_classes(self.anno_file)

        for _, row in self.anno_file.iterrows():
            center = [*map(int, row['cx':'cy'])]
            main_class, middle_class, usable = row['main_class'], row['middle_class'], row['usable']
            label, color = get_label_and_color(main_class, middle_class)
            draw_true_label = self.t_check.isChecked() and usable == 'T'
            draw_false_label = self.f_check.isChecked() and usable == 'F'

            if draw_true_label or draw_false_label:
                if 0 in self.checked_list:
                    cv2.circle(canvas, center, 1, color, thickness * 3)
                if 1 in self.checked_list:
                    points = [list(row[f'x{i}':f'y{i}']) for i in range(1, 5)]
                    polygon = np.array([points], dtype=np.int32)
                    cv2.polylines(canvas, [polygon], True, color, thickness)
                if 2 in self.checked_list:
                    max_points = (int(row['max_x']), int(row['max_y']))
                    min_points = (int(row['min_x']), int(row['min_y']))
                    cv2.rectangle(canvas, min_points, max_points, color, 2)
                if any(x in self.checked_list for x in [3, 4]):
                    cv2.putText(canvas, label, (center[0] + 10, center[1] + 5), 0, 0.6, color, thickness)
                if 5 in self.checked_list:
                    id_label = row['id'].replace('id_', '')
                    cv2.putText(canvas, id_label, (center[0] + 5, center[1] + 5), 0, 0.6, color, thickness)

        return canvas

    def set_scale_and_policy(self, canvas_):
        self.pixmap = QPixmap(q2n.array2qimage(canvas_, normalize=False))
        self.lbl_img.setPixmap(self.pixmap)
        self.lbl_img.setScaledContents(True)
        self.lbl_img.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def goto_scene(self):
        max_length = self.ds.get_max_name_length()
        scene_name = self.goto_input.text().zfill(max_length)
        if scene_name not in self.ds.get_scene_name_list():
            self.goto_input.setText('Not Found')
            return
        self.ds.set_scene_name(scene_name)
        if self.auto_radio.isChecked():
            self.auto_plot_index = 0
            self.ds.current_view_idx = str(self.angle[self.auto_plot_index])
            self.ds.set_view_name(self.ds.current_view_idx)
        else:
            self.ds.set_view_name(str(self.ds.base_view_idx))
        self.change_image_at_scene()

    def filter_non_supported_classes(self, anno_file):
        support_class_set = set(self.supported_classes)
        main_class_set = set(list(anno_file['main_class']))
        non_supported_class_set = main_class_set - support_class_set
        for non_supported_class in non_supported_class_set:
            anno_file = anno_file[anno_file['main_class'] != non_supported_class]
        anno_file = anno_file.dropna()
        anno_file = anno_file.reset_index(drop=True)
        # print(anno_file)
        return anno_file

    def not_found_warning(self, is_eo_valid, is_ir_valid):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)

        path = self.ds.get_view_path()
        eo_files = self.is_eo_valid(path)
        ir_files = self.is_ir_valid(path)

        msg.setText("Please check the files. (EO: {}, IR: {})".format(eo_files[0], ir_files[0]))
        msg.setWindowTitle("Warning")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    @util.scene_navigation
    def goto_prev_scene(self, idx, length):
        new_idx = idx - 1
        return new_idx if new_idx >= 0 else length - 1

    @util.scene_navigation
    def goto_next_scene(self, idx, length):
        new_idx = idx + 1
        return new_idx if new_idx < length else 0

    @util.scene_navigation
    def goto_first_scene(self, idx, length):
        return 0

    def goto_view(self):
        self.ds.set_view_name(str(self.angle[self.view_group.checkedId()]))
        self.change_image_at_view()

    @util.view_navigation
    def goto_prev_view(self, view_names, idx):
        if idx == 0:
            return None
        return str(view_names[idx - 1])

    @util.view_navigation
    def goto_next_view(self, view_names, idx):
        if idx == len(view_names) - 1:
            return None
        return str(view_names[idx + 1])

    @util.view_navigation
    def goto_base_view(self, view_names, idx):
        return self.ds.base_view_idx

    def save_png(self):
        file_name = QFileDialog.getSaveFileName(self, 'Save File', '', 'PNG(*.png)')[0]
        if file_name:
            self.pixmap.save(file_name, 'png')

    def save_plot(self, format_):
        assert format_ in ['svg', 'pdf']
        img = mpimg.imread(self.ds.get_eo_path())
        self.anno_file = self.ds.get_eo_csv()
        self.anno_file = self.filter_non_supported_classes(self.anno_file)

        fig = plt.figure(frameon=False)
        ax = plt.Axes(fig, [0., 0., 1., 1.], )
        ax.set_axis_off()
        fig.add_axes(ax)
        ax.imshow(img, aspect='auto')

        legends_labels, colors, lines, labelss = [], [], [], []
        for _, row in self.anno_file.iterrows():
            center = [*map(float, row['cx':'cy'])]
            main_class, middle_class, usable = row['main_class'], row['middle_class'], row['usable']
            draw_true_label = self.t_check.isChecked() and usable == 'T'
            draw_false_label = self.f_check.isChecked() and usable == 'F'

            if draw_true_label or draw_false_label:
                if 4 not in self.checked_list:
                    label = main_class
                    color = self.FIXED_COLOR_STYLE[main_class][0]
                else:
                    label = main_class if main_class == middle_class else f'{main_class}:{middle_class}'
                    color = self.FIXED_COLOR_STYLE[label][0]
                color = np.array(color) / 255
                line_style = self.FIXED_COLOR_STYLE[label][1]

                if 0 in self.checked_list:
                    ax.scatter(*center, s=30, c=color)
                if 1 in self.checked_list:
                    points = [list(row[f'x{i}':f'y{i}']) for i in range(1, 5)]
                    polygon = patches.Polygon(points, closed=True, ec=color, fill=False, lw=1, ls=line_style)
                    ax.add_patch(polygon)
                if 2 in self.checked_list:
                    min_points = (int(row['min_x']), int(row['min_y']))
                    width, height = int(row['max_x']) - min_points[0], int(row['max_y']) - min_points[1]
                    rect = plt.Rectangle(min_points, width, height, ec=color, fill=False, lw=1, ls=line_style)
                    ax.add_patch(rect)
                if 5 in self.checked_list:
                    id_label = row['id'].replace('id_', '')
                    ax.text(center[0] + 5, center[1] + 5, id_label, c=color, fontsize=10, ha='center', va='center')

                if label not in legends_labels:
                    legends_labels.append(label)
                    colors.append(color)

        for li, la in sorted(zip(legends_labels, colors)):
            lines.append(plt.Line2D([0, 0], [0, 0], c=la, lw=1, ls=self.FIXED_COLOR_STYLE[li][1]))
            labelss.append(li)

        font_prop = FontProperties(family='Cambria')
        legend = ax.legend(lines, labelss, framealpha=0.7, prop=font_prop)
        legend.get_frame().set_boxstyle("round, pad=0.2")
        legend.get_frame().set_edgecolor('gray')
        ax.add_artist(legend)

        file_name = QFileDialog.getSaveFileName(self, 'Save File', '', f'{format_.upper()}(*.{format_.lower()})')[0]
        if file_name:
            fig.savefig(file_name, format=format_, bbox_inches='tight', pad_inches=0)

    def save_gif(self):
        frames = []

        for i in self.angle:
            folder_path = pth.join(self.ds.get_scene_path(), str(i))
            png_files = glob.glob(os.path.join(folder_path, '*.png'))[0]
            canvas = cv2.imread(png_files)
            canvas = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
            canvas = self.plot_canvas(canvas, folder_path)
            if canvas.dtype != np.uint8:
                canvas = canvas.astype(np.uint8)
            frames.append(canvas)

        file_name = QFileDialog.getSaveFileName(self, 'Save File', '', f'GIF(*.gif)')[0]
        if file_name:
            writer = imageio.get_writer(f'{file_name}', mode='I', duration=500, loop=0,
                                        plugin='pillow', subrectangles=True)
            for array in frames:
                writer.append_data(array)
            writer.close()

    def remark_sort(self):
        scene_path_list, metacsv_file = self.ds.get_scene_path_list(), self.ds.get_metacsv()
        set_path = self.ds.get_set_path()
        sorted_data = metacsv_file.sort_values(by=['remarks', 'i_time'], ascending=True)
        sorted_scene_paths = []
        for i, row in sorted_data.iterrows():
            if i == len(scene_path_list):
                break
            sorted_scene_paths.append(pth.join(set_path, row['i_time']))
        self.ds.set_scene_path_list(sorted_scene_paths)

    def auto_plot(self):
        self.auto_plot_index = 0
        self.auto_plot_timer.start(500)

    def auto_plot_step(self):
        if self.auto_plot_index < len(self.angle):
            self.ds.current_view_idx = str(self.angle[self.auto_plot_index])
            self.ds.set_view_name(self.ds.current_view_idx)
            self.change_image_at_view()
            self.auto_plot_index += 1
        else:
            self.auto_plot_index = 0

    def create_report_dialog(self):
        text, ok = QInputDialog.getMultiLineText(self, 'Report', "What\'s the issue?")
        if ok:
            with open(pth.join(self.ds.get_set_path(), 'report.csv'), 'a') as f:
                f.write(f'{self.ds.get_scene_path()},{datetime.now().strftime("%Y%m%d%H%M")}.,{text}\n')

    def keyPressEvent(self, e):
        if e.key() in self.key_map:
            self.key_map[e.key()]()


if __name__ == '__main__':
    if os.path.basename(os.getcwd()) == 'src':
        os.chdir('..')
    viewer = QApplication(sys.argv)
    viewer.setWindowIcon(QIcon('figs/AMOD-Viewer-Icon.svg'))
    ex = ArmaViewer()
    sys.exit(viewer.exec_())
