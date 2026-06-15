import pandas as pd

from invoice import *

class AnomalyPipeline:
    def __init__(self):
        self.df_invoices = None
        self.df_invoices_lines = None
        self.invoices = []
        self.invalid_invoices = []

    def load_data(self, df_invoices_path, df_invoices_lines_path):
        self.df_invoices = pd.read_csv(df_invoices_path)
        self.df_invoices['total_net'] = (self.df_invoices["total_net"] * 100).round().astype(int)
        self.df_invoices['total_gross'] = (self.df_invoices["total_gross"] * 100).round().astype(int)

        self.df_invoices_lines = pd.read_csv(df_invoices_lines_path)
        self.df_invoices_lines['unit_price_net'] = (self.df_invoices_lines["unit_price_net"] * 100).round().astype(int)
        self.df_invoices_lines['line_net'] = (self.df_invoices_lines["line_net"] * 100).round().astype(int)
        self.df_invoices_lines['line_gross'] = (self.df_invoices_lines["line_gross"] * 100).round().astype(int)


    def build_invoices(self):
        for invoice_id, lines_df in self.df_invoices_lines.groupby("invoice_id"):
            lines = []

            for _, row in lines_df.iterrows():
                invoice_line = InvoiceLine(
                    invoice_id = row['invoice_id'],
                    line_no = row['line_no'],
                    service_name = row['service_name'],
                    service_category = row['service_category'],
                    quantity = row['quantity'],
                    unit_price_net = row['unit_price_net'],
                    line_net = row['line_net'],
                    line_gross = row['line_gross'],
                    vat_rate = row['vat_rate']
                )
                lines.append(invoice_line)

            invoice_row = self.df_invoices[self.df_invoices['invoice_id'] == invoice_id]

            if len(invoice_row) == 0:
                self.invalid_invoices.append((invoice_id, 'missing_invoice'))
                continue

            if len(invoice_row) > 1:
                self.invalid_invoices.append((invoice_id, 'duplicated_invoice'))
                print('DUPLIKAT WYKRYTY')
                continue
                ## trzeba się lepiej przyjrzeć duplikatom

            invoice_row = invoice_row.iloc[0]

            invoice = Invoice(
                invoice_id = invoice_row['invoice_id'],
                invoice_date = invoice_row['invoice_date'],
                invoice_number = invoice_row['invoice_number'],
                sender_nip = invoice_row['sender_nip'],
                recipient_nip = invoice_row['recipient_nip'],
                sender_name = invoice_row['sender_name'],
                recipient_name = invoice_row['recipient_name'],
                total_net = invoice_row['total_net'],
                total_gross = invoice_row['total_gross'],
                currency = invoice_row['currency'],
                payment_due_date = invoice_row['payment_due_date'],
                risk_score = invoice_row['risk_score'],
                audit_passed = invoice_row['audit_passed'],
                lines = lines
            )
            self.invoices.append(invoice)




