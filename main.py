import pandas as pd
from pipeline import AnomalyPipeline
from train_pipeline import TrainPipeline

pipeline = AnomalyPipeline()
pipeline.load_data('data/val_invoices.csv', 'data/val_invoice_lines.csv')
pipeline.prepare_data()
pipeline.build_invoices()
pipeline.load_model()
types, details = pipeline.detect_anomalies()
pipeline.create_predictions(types, details)

# pipeline = TrainPipeline()
# pipeline.load_train_data('data/train_invoices.csv', 'data/train_labels.csv')
# pipeline.prepare_train_data()
# pipeline.build_train_data()
# pipeline.train_model()