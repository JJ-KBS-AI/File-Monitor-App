# tests/conftest.py — pytest 픽스처
import os
import sys

import pytest

# 프로젝트 루트를 path에 추가 (pytest.ini pythonpath 미적용 시 대비)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


@pytest.fixture
def sample_watch_dir(tmp_path):
    """감시 대상 확장자(.mxf, .mov, .xmp) 샘플 파일이 있는 임시 디렉터리."""
    (tmp_path / "test.mxf").write_text("mxf dummy")
    (tmp_path / "test.mov").write_text("mov dummy")
    (tmp_path / "test.xmp").write_text("xmp dummy")
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "nested.mxf").write_text("nested")
    return tmp_path


@pytest.fixture
def sample_watch_dir_ignore(tmp_path):
    """감시 대상이 아닌 확장자만 있는 디렉터리 (워커가 0건 반환해야 함)."""
    (tmp_path / "readme.txt").write_text("text")
    (tmp_path / "image.jpg").write_text("image")
    return tmp_path
