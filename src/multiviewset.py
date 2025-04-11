#
# multiviewset.py
# arma-rs-utils
#
# Created by Junggyun Oh on 04/04/2023.
# Copyright (c) 2023 Junggyun Oh All rights reserved.
#
import os
import os.path as pth
import pandas as pd
import numpy as np


class MultiViewSet:
    """
    A class representing a dataset.

    Attributes:
        __set_path (str): The path to the dataset directory.
        __set_name (str): The name of the dataset directory.
        __current_scene_idx (int): The index of the current scene.
        __current_view_idx (str): The name of the current view.
        __scene_path_list (list of str): A list of paths to the scenes in the dataset.
        __view_path_list (list of str): A list of paths to the views in the current scene.
    """
    def __init__(self, base_scene_idx=0, base_view_idx='0'):
        self.__set_path = ''
        self.__set_name = ''
        self.__scene_name = ''
        self.__current_scene_idx = base_scene_idx   # e.g. 0
        self.__current_view_idx = base_view_idx     # e.g. '0'
        self.__scene_path_list = []
        self.__scene_name_list = []
        self.__view_path_list = []
        self.base_view_idx = base_view_idx     # e.g. '0'

    def get_set_path(self): return self.__set_path
    def set_set_path(self, path): self.__set_path = path
    def get_set_name(self): return self.__set_name
    def set_set_name(self, name): self.__set_name = name
    def get_scene_index(self): return self.__current_scene_idx
    def set_scene_index(self, idx): self.__current_scene_idx = idx
    def get_view_name(self): return self.__current_view_idx
    def set_view_name(self, name): self.__current_view_idx = name
    def get_max_name_length(self): return len(self.__scene_name_list[0])

    def get_scene_name(self):
        return self.__scene_name_list[self.__current_scene_idx]

    def set_scene_name(self, name):
        self.__current_scene_idx = self.__scene_name_list.index(name)

    def get_scene_name_list(self):
        return self.__scene_name_list

    def get_scene_path(self):
        return self.__scene_path_list[self.__current_scene_idx]

    def get_view_path(self):
        return pth.join(self.__scene_path_list[self.__current_scene_idx], self.__current_view_idx)

    # def get_view_path_xz(self):
    #     return pth.join(self.__scene_path_list[self.__current_scene_idx], '1')

    def get_set_metacsv_path(self):
        set_path = self.get_set_path()
        return next((pth.join(set_path, i) for i in os.listdir(set_path) if 'meta' in i), None)

    def get_metacsv(self):
        return pd.read_csv(self.get_set_metacsv_path(), dtype={'i_time': np.str})

    def get_eo_annotation_path(self):
        view_path = self.get_view_path()
        return next((pth.join(view_path, i) for i in os.listdir(view_path) if 'ANNOTATION-EO' in i and i.endswith('.csv')), None)

    # def get_annotation_path_xz(self):
    #     view_path = self.get_view_path_xz()
    #     return next((pth.join(view_path, i) for i in os.listdir(view_path) if 'ANNOTATION' in i), None)

    def get_ir_annotation_path(self):
        view_path = self.get_view_path()
        return next((pth.join(view_path, i) for i in os.listdir(view_path) if 'ANNOTATION-IR' in i and i.endswith('.csv')), None)

    def get_eo_csv(self):
        return pd.read_csv(self.get_eo_annotation_path())

    # def get_csv_xz(self):
    #     return pd.read_csv(self.get_annotation_path_xz())

    def get_ir_csv(self):
        return pd.read_csv(self.get_ir_annotation_path())

    def get_eo_path(self):
        view_path = self.get_view_path()
        return next((pth.join(view_path, i) for i in os.listdir(view_path) if 'EO' in i and i.endswith('.png')), None)

    # def get_eo_path_xz(self):
    #     view_path = self.get_view_path_xz()
    #     return next((pth.join(view_path, i) for i in os.listdir(view_path) if 'EO' in i), None)

    def get_ir_path(self):
        view_path = self.get_view_path()
        return next((pth.join(view_path, i) for i in os.listdir(view_path) if 'IR' in i and i.endswith('png')), None)

    def get_scene_path_list(self):
        return self.__scene_path_list

    def set_scene_path_list(self, path_list):
        self.__scene_path_list = path_list

    def get_view_name_path_list(self):
        """Get view names and their corresponding paths."""
        scene_path = self.get_scene_path()
        view_name_list = sorted(list(map(int, [pth.basename(i) for i in os.listdir(scene_path)])))
        __view_path_list = [pth.join(scene_path, str(i)) for i in view_name_list]
        return view_name_list, __view_path_list

    def set_path_and_name(self, path):
        self.__set_path = path
        self.__set_name = pth.basename(path)

        base_list = []
        for f in os.listdir(path):
            try:
                if int(f) or f in ['0', '00', '000', '0000']:
                    base_list.append(f)
            except ValueError:
                pass
        scene_list = [os.path.join(path, f) for f in base_list]
        self.__scene_path_list = sorted(scene_list)
        self.__scene_name_list = sorted(base_list)

    def update_best_view_idx(self):
        try:
            look_angles = os.listdir(self.__scene_path_list[0])
            median_idx = int(len(look_angles) / 2)
            if self.__current_view_idx != look_angles[median_idx]:
                print(f'current_view_idx (base_look_angle) {self.__current_view_idx} '
                      f'has been replaced with {look_angles[median_idx]}')
                self.__current_view_idx = look_angles[median_idx]
                self.base_view_idx = look_angles[median_idx]
            return self.__current_view_idx
        except Exception as e:
            print('error at __update_best_view_idx() in multiviewset.py')
            print('detailed error message: \n', e)
            return 0
