import pandas as pd
from pipeline import *

pipeline = AnomalyPipeline()
pipeline.load_data('data/test_invoices.csv', 'data/test_invoice_lines.csv')
pipeline.build_invoices()