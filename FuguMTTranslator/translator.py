"""
FuguMT翻訳エンジン

FuguMTモデルを使用した翻訳処理を行います。
"""

import logging
import time
import torch
from transformers import MarianMTModel, MarianTokenizer
from typing import Dict, List, Optional, Tuple
import threading


class FuguMTTranslator:
    """FuguMT翻訳エンジン"""
    
    def __init__(self, config):
        """
        翻訳エンジンの初期化
        
        Args:
            config: 設定オブジェクト
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # デバイス設定
        self.device = self._setup_device()
        self.logger.info(f"使用デバイス: {self.device}")
        
        # FP16設定
        self.use_fp16 = self.config.use_fp16 and self.device != 'cpu'
        if self.use_fp16:
            self.logger.info("FP16モードを有効にしました")
        else:
            self.logger.info("FP32モードを使用します")
        
        # モデルとトークナイザーの初期化
        self.models = {}
        self.tokenizers = {}
        self._load_models()
        
        # 統計情報
        self.stats = {
            'total_translations': 0,
            'total_tokens': 0,
            'total_time': 0.0,
            'error_count': 0
        }
        self.stats_lock = threading.Lock()
        
    def cleanup(self):
        """リソースクリーンアップ"""
        try:
            self.logger.info("翻訳エンジンのクリーンアップを開始します...")
            
            # モデルをCPUに移動してメモリ解放
            for model_name, model in self.models.items():
                if hasattr(model, 'cpu'):
                    model.cpu()
                del model
                self.logger.debug(f"モデル {model_name} を解放しました")
            
            # モデル辞書をクリア
            self.models.clear()
            self.tokenizers.clear()
            
            # CUDAキャッシュクリア
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
                self.logger.debug("CUDAキャッシュをクリアしました")
            
            # ガベージコレクション実行
            import gc
            gc.collect()
            
            self.logger.info("翻訳エンジンのクリーンアップが完了しました")
            
        except Exception as e:
            self.logger.warning(f"クリーンアップ中にエラー: {e}")
        
    def _setup_device(self):
        """デバイス設定"""
        device_config = self.config.device.lower()
        gpu_id_config = self.config.gpu_id.lower()
        
        if device_config == 'auto':
            if torch.cuda.is_available():
                device = 'cuda'
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return 'mps'
            else:
                return 'cpu'
        else:
            device = device_config
            
        # CUDA使用時のGPU ID指定
        if device == 'cuda' and torch.cuda.is_available():
            if gpu_id_config != 'auto':
                try:
                    gpu_id = int(gpu_id_config)
                    gpu_count = torch.cuda.device_count()
                    
                    if 0 <= gpu_id < gpu_count:
                        device = f'cuda:{gpu_id}'
                        self.logger.info(f"指定されたGPU {gpu_id} を使用します")
                    else:
                        self.logger.warning(f"無効なGPU ID: {gpu_id}. 利用可能なGPU数: {gpu_count}. 自動選択します。")
                        device = 'cuda'
                except ValueError:
                    self.logger.warning(f"無効なGPU ID設定: {gpu_id_config}. 自動選択します。")
                    device = 'cuda'
            
            # 選択されたGPUの情報をログ出力
            if device.startswith('cuda:'):
                gpu_id = int(device.split(':')[1])
                gpu_name = torch.cuda.get_device_name(gpu_id)
                gpu_memory = torch.cuda.get_device_properties(gpu_id).total_memory / (1024**3)
                self.logger.info(f"使用GPU: {gpu_name} ({gpu_memory:.1f}GB)")
            elif device == 'cuda':
                current_gpu = torch.cuda.current_device()
                gpu_name = torch.cuda.get_device_name(current_gpu)
                gpu_memory = torch.cuda.get_device_properties(current_gpu).total_memory / (1024**3)
                self.logger.info(f"使用GPU: {gpu_name} ({gpu_memory:.1f}GB) [自動選択]")
                
        return device
            
    def _load_models(self):
        """モデルとトークナイザーの読み込み"""
        try:
            self.logger.info("FuguMTモデルを読み込み中...")
            
            # 英日翻訳モデル
            if self.config.model_name_en_ja:
                self.logger.info(f"英日モデル読み込み: {self.config.model_name_en_ja}")
                self.tokenizers['en-ja'] = MarianTokenizer.from_pretrained(
                    self.config.model_name_en_ja
                )
                model = MarianMTModel.from_pretrained(
                    self.config.model_name_en_ja
                ).to(self.device)
                
                # FP16モードの適用
                if self.use_fp16:
                    model = model.half()
                    self.logger.info("英日モデルをFP16モードに設定しました")
                
                self.models['en-ja'] = model
                self.models['en-ja'].eval()
                
            # 日英翻訳モデル（存在する場合）
            if self.config.model_name_ja_en:
                try:
                    self.logger.info(f"日英モデル読み込み: {self.config.model_name_ja_en}")
                    self.tokenizers['ja-en'] = MarianTokenizer.from_pretrained(
                        self.config.model_name_ja_en
                    )
                    model = MarianMTModel.from_pretrained(
                        self.config.model_name_ja_en
                    ).to(self.device)
                    
                    # FP16モードの適用
                    if self.use_fp16:
                        model = model.half()
                        self.logger.info("日英モデルをFP16モードに設定しました")
                    
                    self.models['ja-en'] = model
                    self.models['ja-en'].eval()
                except Exception as e:
                    self.logger.warning(f"日英モデルの読み込みに失敗: {e}")
                    
            self.logger.info("モデル読み込み完了")
            
        except Exception as e:
            self.logger.error(f"モデル読み込みエラー: {e}")
            raise
            
    def translate(self, text: str, source_lang: str = 'en', target_lang: str = 'ja') -> Dict:
        """
        テキストを翻訳する
        
        Args:
            text (str): 翻訳対象テキスト
            source_lang (str): 源言語 ('en' または 'ja')
            target_lang (str): 目標言語 ('ja' または 'en')
            
        Returns:
            Dict: 翻訳結果
        """
        start_time = time.time()
        
        try:
            # 言語ペアの確認
            lang_pair = f"{source_lang}-{target_lang}"
            
            if lang_pair not in self.models:
                available_pairs = list(self.models.keys())
                raise ValueError(f"サポートされていない言語ペア: {lang_pair}. 利用可能: {available_pairs}")
                
            # モデルとトークナイザーの取得
            model = self.models[lang_pair]
            tokenizer = self.tokenizers[lang_pair]
            
            # テキストの前処理とトークン化
            if not text.strip():
                raise ValueError("翻訳対象テキストが空です")
                
            inputs = tokenizer(
                text,
                return_tensors="pt",
                max_length=self.config.max_length,
                truncation=True,
                padding=True
            ).to(self.device)
            
            # FP16モードの場合、入力も半精度に変換
            if self.use_fp16:
                inputs = {k: v.half() if v.dtype == torch.float32 else v for k, v in inputs.items()}
            
            # 翻訳実行
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_length=self.config.max_length,
                    num_beams=self.config.num_beams,
                    temperature=self.config.temperature,
                    do_sample=self.config.temperature != 1.0,
                    use_cache=self.config.use_cache,
                    early_stopping=True
                )
                
            # 結果のデコード
            translated_text = tokenizer.decode(
                outputs[0], 
                skip_special_tokens=True
            )
            
            # 処理時間計算
            processing_time = time.time() - start_time
            
            # 統計更新
            with self.stats_lock:
                self.stats['total_translations'] += 1
                self.stats['total_tokens'] += len(inputs['input_ids'][0])
                self.stats['total_time'] += processing_time
                
            return {
                'translated_text': translated_text,
                'source_text': text,
                'source_lang': source_lang,
                'target_lang': target_lang,
                'processing_time_ms': processing_time * 1000,
                'status': 'success'
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"翻訳エラー: {e}")
            
            with self.stats_lock:
                self.stats['error_count'] += 1
                
            return {
                'error': str(e),
                'source_text': text,
                'source_lang': source_lang,
                'target_lang': target_lang,
                'processing_time_ms': processing_time * 1000,
                'status': 'error'
            }
            
    def get_stats(self) -> Dict:
        """統計情報の取得"""
        with self.stats_lock:
            stats = self.stats.copy()
            
        # 平均処理時間を計算
        if stats['total_translations'] > 0:
            stats['avg_processing_time'] = stats['total_time'] / stats['total_translations']
            stats['avg_tokens_per_translation'] = stats['total_tokens'] / stats['total_translations']
        else:
            stats['avg_processing_time'] = 0.0
            stats['avg_tokens_per_translation'] = 0.0
            
        return stats
        
    def get_supported_languages(self) -> List[str]:
        """サポートされている言語ペアの取得"""
        return list(self.models.keys())
        
    def health_check(self) -> Dict:
        """ヘルスチェック"""
        try:
            # 簡単な翻訳テスト
            test_result = self.translate("Hello", "en", "ja")
            
            return {
                'status': 'healthy',
                'models_loaded': len(self.models),
                'supported_pairs': self.get_supported_languages(),
                'device': self.device,
                'fp16_mode': self.use_fp16,
                'test_translation': test_result.get('status') == 'success'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'models_loaded': len(self.models),
                'device': self.device,
                'fp16_mode': self.use_fp16
            }