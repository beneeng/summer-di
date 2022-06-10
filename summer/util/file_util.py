

from contextlib import contextmanager
from io import FileIO
import os
import shutil
import tempfile
from typing import ContextManager
import uuid


@contextmanager
def open_with_backup(path, *args, **kwargs) -> ContextManager[FileIO]:
    tmp_filename = f"{uuid.uuid4()}.bak"
    tmp_filepath = os.path.join(tempfile.gettempdir(), tmp_filename)
    try:
        if os.path.exists(path):
            shutil.copy2(path, tmp_filepath)
        with open(path, *args, **kwargs) as f:
            yield f
    except:
        if os.path.exists(tmp_filepath):
            shutil.copy2(tmp_filepath, path)
        raise
    finally:
        if os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)
