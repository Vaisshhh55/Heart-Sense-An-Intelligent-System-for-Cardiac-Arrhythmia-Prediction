import os
from clinical_compliance import HIPAACompliance
import logging

logger = logging.getLogger('cardiac.verify_hipaa')
if not logger.handlers:
	h = logging.StreamHandler()
	h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
	logger.addHandler(h)
	logger.setLevel(logging.INFO)

base_dir = os.path.dirname(os.path.abspath(__file__))
h = HIPAACompliance(os.path.join(base_dir, 'hipaa_compliance.db'))
logger.info('%s', h.get_compliance_status())
logger.info('%s', h.get_audit_log(5))
