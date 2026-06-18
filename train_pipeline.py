import pandas as pd

from invoice import Invoice, InvoiceLine
from detector import BaseDetector, SumMismatch, VatError, NearDuplicate, AmountOutlier

class TrainPipeline:
    def __init__(self):
        self.df_invoices = None
        self.invoices = []
        self.labels = None


    def load_train_data(self, df_invoices_path, labels_path):
        self.df_invoices = pd.read_csv(df_invoices_path)
        self.df_invoices['total_net'] = (self.df_invoices["total_net"] * 100).round().astype(int)
        self.df_invoices['total_gross'] = (self.df_invoices["total_gross"] * 100).round().astype(int)
        self.df_invoices['invoice_date'] = pd.to_datetime(self.df_invoices['invoice_date'], format='%Y-%m-%d')

        self.labels = pd.read_csv(labels_path)


    def prepare_train_data(self):
        self.df_invoices = self.df_invoices.drop_duplicates()

        dup_headers = self.df_invoices[self.df_invoices.duplicated(subset=['invoice_id'], keep=False)]
        dup_counts = dup_headers.groupby('invoice_id').size()
        bad_ids = set(dup_counts.index)

        if bad_ids:
            print(f"Removed duplicated invoices ID: {bad_ids}.")
            self.df_invoices = self.df_invoices[~self.df_invoices['invoice_id'].isin(bad_ids)]


    def build_train_data(self):
        for _, invoice_row in self.df_invoices.iterrows():
            invoice = Invoice(
                invoice_id=invoice_row['invoice_id'],
                invoice_date=invoice_row['invoice_date'],
                invoice_number=invoice_row['invoice_number'],
                sender_nip=invoice_row['sender_nip'],
                recipient_nip=invoice_row['recipient_nip'],
                sender_name=invoice_row['sender_name'],
                recipient_name=invoice_row['recipient_name'],
                total_net=invoice_row['total_net'],
                total_gross=invoice_row['total_gross'],
                currency=invoice_row['currency'],
                payment_due_date=invoice_row['payment_due_date'],
                risk_score=invoice_row['risk_score'],
                audit_passed=invoice_row['audit_passed'],
                lines=[]
            )

            self.invoices.append(invoice)

        self.labels["is_amount_outlier"] = self.labels["anomaly_types"].fillna("").apply(
            lambda x: 1 if "amount_outlier" in x else 0
        )
        self.labels = dict(zip(self.labels["invoice_id"], self.labels["is_amount_outlier"]))


    def train_model(self):
        train = AmountOutlier()
        train.fit(self.invoices, self.labels)