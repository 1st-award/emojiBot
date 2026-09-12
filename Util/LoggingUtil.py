import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging():
    """LOG_LEVEL 환경 변수로 콘솔과 순환 파일 로깅을 설정한다.

    기본 레벨은 INFO이며 잘못된 값은 ValueError로 거부한다. 기존 루트 핸들러를
    교체하고 logs/bot.log를 5MiB 단위로 순환하여 이전 파일 3개를 보관한다.
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL")
    log_dir = Path(__file__).resolve().parents[1] / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), RotatingFileHandler(
            log_dir / "bot.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")],
        force=True,
    )
    logging.getLogger("discord").setLevel(logging.INFO)
