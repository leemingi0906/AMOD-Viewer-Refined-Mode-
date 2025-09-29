# annotation_object.py

import numpy as np
import pandas as pd
from typing import Dict, Any

class AnnotationObject:
    def __init__(self, row_data: pd.Series, transform_data: Dict[str, Any]):
        self.row_data = row_data
        self.id = row_data['id']
        self.original_points = np.array([
            [row_data['x1'], row_data['y1']],
            [row_data['x2'], row_data['y2']],
            [row_data['x3'], row_data['y3']],
            [row_data['x4'], row_data['y4']]
        ], dtype=np.float32) # 원본 좌표는 float32로 저장

        self.is_selected = False
        self.is_modified = False

        # 변환 데이터 초기화
        self.transform_data = transform_data
        self.reset_transform() # 변환 데이터를 0으로 초기화


    def get_transformed_points(self):
        # 변환 행렬 생성
        tx, ty = self.transform_data['translate_x'], self.transform_data['translate_y']
        sw, sh = self.transform_data['scale_w'], self.transform_data['scale_h']
        angle_rad = np.deg2rad(self.transform_data['angle'])

        # 1. 중심을 (0,0)으로 이동
        center_x, center_y = np.mean(self.original_points, axis=0)
        temp_points = self.original_points - np.array([center_x, center_y])

        # 2. 스케일 적용
        scale_matrix = np.array([[sw, 0], [0, sh]])
        scaled_points = np.dot(temp_points, scale_matrix)

        # 3. 회전 적용
        rotation_matrix = np.array([
            [np.cos(angle_rad), -np.sin(angle_rad)],
            [np.sin(angle_rad), np.cos(angle_rad)]
        ])
        rotated_points = np.dot(scaled_points, rotation_matrix)

        # 4. 다시 원래 중심으로 이동 후, 이동(translate) 적용
        transformed_points = rotated_points + np.array([center_x + tx, center_y + ty])
        
        return transformed_points.astype(np.int32) # 항상 정수로 반환

    def reset_transform(self):
        self.transform_data['translate_x'] = 0.0
        self.transform_data['translate_y'] = 0.0
        self.transform_data['scale_w'] = 1.0
        self.transform_data['scale_h'] = 1.0
        self.transform_data['angle'] = 0.0
        self.is_modified = False

    def apply_transform_to_original(self):
        """현재 변환된 상태를 original_points에 적용하고 변환을 리셋합니다."""
        self.original_points = self.get_transformed_points().astype(np.float32)
        self.reset_transform()
        self.is_modified = False # 수정 완료 후 수정 상태 해제