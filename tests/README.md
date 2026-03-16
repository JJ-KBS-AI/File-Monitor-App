# 테스트 환경

## 설치

```bash
pip install -r requirements-dev.txt
```

## 실행

프로젝트 루트에서:

```bash
pytest
```

Windows에서 `pytest`가 PATH에 없으면:

```bash
py -m pytest
```

또는:

```bash
run_tests.bat
```

특정 파일만 실행:

```bash
pytest tests/test_constants.py -v
pytest tests/test_folder_checker.py -v
pytest tests/test_preset.py -v
```

## 테스트 구성

| 파일 | 내용 |
|------|------|
| `conftest.py` | 픽스처: `sample_watch_dir`(mxf/mov/xmp 샘플), `sample_watch_dir_ignore`(미감시 확장자만) |
| `test_constants.py` | 상수·매핑 검증 (PRESET_KEYS, NOTIFICATION_MESSAGES, WATCH_EXTENSIONS 등) |
| `test_folder_checker.py` | `FolderCheckerWorker` 스캔 결과 시그널 검증 |
| `test_preset.py` | 프리셋 저장/불러오기 및 JSON 구조 검증 |
