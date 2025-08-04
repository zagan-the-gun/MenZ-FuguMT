"""
設定管理モジュール

FuguMT翻訳サーバーの設定を管理します。
"""

import os
import configparser
from pathlib import Path
import logging


class Config:
    """設定管理クラス"""
    
    def __init__(self, config_path=None):
        """
        設定初期化
        
        Args:
            config_path (str, optional): 設定ファイルのパス
        """
        self.config_path = config_path or "config/fugumt_translator.ini"
        self.config = configparser.ConfigParser()
        self._create_directories()
        self._load_or_create_config()
        
    def _create_directories(self):
        """必要なディレクトリを作成"""
        for directory in ["config", "logs"]:
            Path(directory).mkdir(exist_ok=True)
            
    def _load_or_create_config(self):
        """設定ファイルの読み込みまたは作成"""
        if os.path.exists(self.config_path):
            self.config.read(self.config_path, encoding='utf-8')
            self._validate_config()
        else:
            self._create_default_config()
            
    def _create_default_config(self):
        """デフォルト設定ファイルの作成"""
        self.config['SERVER'] = {
            'host': '127.0.0.1',
            'port': '55002',
            'max_connections': '50'
        }
        
        self.config['TRANSLATION'] = {
            'model_name_en_ja': 'staka/fugumt-en-ja',
            'model_name_ja_en': 'staka/fugumt-ja-en',  # もし利用可能であれば
            'device': 'auto',  # auto, cpu, cuda, mps
            'gpu_id': 'auto',  # GPU ID (cudaデバイス使用時のみ有効): 0, 1, 2... または auto
            'max_length': '512',
            'num_beams': '4',
            'temperature': '1.0',
            'use_cache': 'true',
            'use_fp16': 'false'  # FP16（半精度浮動小数点）モード
        }
        
        self.config['LOGGING'] = {
            'level': 'INFO',
            'file': 'logs/fugumt_translator.log',
            'max_size': '10MB',
            'backup_count': '5'
        }
        
        self.config['PERFORMANCE'] = {
            'batch_size': '1',
            'timeout_seconds': '30.0',
            'worker_threads': '4'
        }
        
        # 設定ファイルを保存
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
            
        print(f"デフォルト設定ファイルを作成しました: {self.config_path}")
        
    def _validate_config(self):
        """設定ファイルの検証"""
        required_sections = ['SERVER', 'TRANSLATION', 'LOGGING', 'PERFORMANCE']
        for section in required_sections:
            if not self.config.has_section(section):
                raise ValueError(f"設定ファイルに必要なセクション '{section}' がありません")
                
    def get(self, section, key, fallback=None):
        """設定値の取得"""
        return self.config.get(section, key, fallback=fallback)
        
    def getint(self, section, key, fallback=None):
        """設定値の取得（整数）"""
        return self.config.getint(section, key, fallback=fallback)
        
    def getfloat(self, section, key, fallback=None):
        """設定値の取得（浮動小数点）"""
        return self.config.getfloat(section, key, fallback=fallback)
        
    def getboolean(self, section, key, fallback=None):
        """設定値の取得（真偽値）"""
        return self.config.getboolean(section, key, fallback=fallback)
        
    @property
    def server_host(self):
        return self.get('SERVER', 'host', '127.0.0.1')
        
    @property
    def server_port(self):
        return self.getint('SERVER', 'port', 55002)
        
    @property
    def max_connections(self):
        return self.getint('SERVER', 'max_connections', 50)
        
    @property
    def model_name_en_ja(self):
        return self.get('TRANSLATION', 'model_name_en_ja', 'staka/fugumt-en-ja')
        
    @property
    def model_name_ja_en(self):
        return self.get('TRANSLATION', 'model_name_ja_en', 'staka/fugumt-ja-en')
        
    @property
    def device(self):
        return self.get('TRANSLATION', 'device', 'auto')
        
    @property
    def gpu_id(self):
        return self.get('TRANSLATION', 'gpu_id', 'auto')
        
    @property
    def max_length(self):
        return self.getint('TRANSLATION', 'max_length', 512)
        
    @property
    def num_beams(self):
        return self.getint('TRANSLATION', 'num_beams', 4)
        
    @property
    def temperature(self):
        return self.getfloat('TRANSLATION', 'temperature', 1.0)
        
    @property
    def use_cache(self):
        return self.getboolean('TRANSLATION', 'use_cache', True)
        
    @property
    def use_fp16(self):
        return self.getboolean('TRANSLATION', 'use_fp16', False)
        
    @property
    def log_level(self):
        return self.get('LOGGING', 'level', 'INFO')
        
    @property
    def log_file(self):
        return self.get('LOGGING', 'file', 'logs/fugumt_translator.log')
        
    @property
    def batch_size(self):
        return self.getint('PERFORMANCE', 'batch_size', 1)
        
    @property
    def timeout_seconds(self):
        return self.getfloat('PERFORMANCE', 'timeout_seconds', 30.0)
        
    @property
    def worker_threads(self):
        return self.getint('PERFORMANCE', 'worker_threads', 4)