"""Package only the loadable extension. No source tools or browser profile data."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
target = root / 'dist' / 'presenter-cursor-chrome-1.0.2.zip'
target.parent.mkdir(exist_ok=True)
with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
    for source in sorted((root / 'extension').rglob('*')):
        if source.is_file():
            archive.write(source, source.relative_to(root / 'extension'))
print(target)
