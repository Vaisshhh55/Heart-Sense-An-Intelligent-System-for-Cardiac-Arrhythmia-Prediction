import os
from pathlib import Path
from datetime import datetime

reports = list(Path('reports').glob('Prediction_*.pdf'))
if not reports:
    print('No reports found')
    raise SystemExit(1)

print('Found reports:')
for p in reports:
    print(p.name, '-', p.stat().st_size, 'bytes')

# Try to extract text using PyPDF2 if available
try:
    import PyPDF2
    for p in reports:
        try:
            with open(p, 'rb') as fh:
                reader = PyPDF2.PdfReader(fh)
                first_page = reader.pages[0]
                text = first_page.extract_text() or ''
                print('\n---- First page text of', p.name, '----')
                print(text[:1000])
        except Exception as e:
            print('Failed to extract from', p.name, e)
except Exception as e:
    print('PyPDF2 not available, skipping text extraction:', e)
