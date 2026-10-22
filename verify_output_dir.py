from CARDIAC_ARRHYTHMIA_UPDATED.report_generator import PDFReportGenerator
import os
p = PDFReportGenerator()
print('Resolved output_dir:', p.output_dir)
print('Exists:', os.path.exists(p.output_dir))
