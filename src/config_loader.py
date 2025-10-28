"""
設定ファイル読み込みユーティリティ
config.yaml から設定を読み込み、辞書として提供する
"""
import os
import yaml
from pathlib import Path


class Config:
    """設定管理クラス（シングルトン）"""
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    def _load_config(self):
        """config.yamlを読み込む"""
        # プロジェクトルートのconfig.yamlを探す
        current_dir = Path(__file__).parent
        config_path = current_dir.parent / "config.yaml"

        if not config_path.exists():
            raise FileNotFoundError(
                f"設定ファイルが見つかりません: {config_path}\n"
                "プロジェクトルートに config.yaml を配置してください。"
            )

        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    def get(self, key_path, default=None):
        """
        ドット区切りのキーパスで設定値を取得

        Args:
            key_path (str): 設定キーのパス（例: "llm.searcher.model"）
            default: デフォルト値

        Returns:
            設定値（見つからない場合はdefault）

        Example:
            config = Config()
            model = config.get("llm.searcher.model")  # "gemini-2.5-flash"
        """
        keys = key_path.split(".")
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_all(self):
        """全設定を辞書として取得"""
        return self._config.copy()


# グローバルインスタンス（簡単にアクセスできるように）
_global_config = None


def get_config():
    """設定インスタンスを取得（推奨される使用方法）"""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def reload_config():
    """設定を再読み込み（テスト用）"""
    global _global_config
    _global_config = None
    Config._instance = None
    Config._config = None
    return get_config()
