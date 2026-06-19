import pandas as pd
from .invoice import Invoice, InvoiceLine
from .detector import BaseDetector, SumMismatch, VatError, NearDuplicate, AmountOutlier

class AnomalyPipeline:
    def __init__(self):
        self.df_invoices = None
        self.df_invoices_lines = None
        self.invoices = []
        self.df_labels = None
        self.labels = []
        self.invalid_invoices = []
        self.amount_outlier = None


    def load_data(self, df_invoices_path, df_invoices_lines_path):
        self.df_invoices = pd.read_csv(df_invoices_path)
        self.df_invoices['total_net'] = (self.df_invoices["total_net"] * 100).round().astype(int)
        self.df_invoices['total_gross'] = (self.df_invoices["total_gross"] * 100).round().astype(int)
        self.df_invoices['invoice_date'] = pd.to_datetime(self.df_invoices['invoice_date'], format='%Y-%m-%d')

        self.df_invoices_lines = pd.read_csv(df_invoices_lines_path)
        self.df_invoices_lines['unit_price_net'] = (self.df_invoices_lines["unit_price_net"] * 100).round().astype(int)
        self.df_invoices_lines['line_net'] = (self.df_invoices_lines["line_net"] * 100).round().astype(int)
        self.df_invoices_lines['line_gross'] = (self.df_invoices_lines["line_gross"] * 100).round().astype(int)


    def prepare_data(self):
        # 1. Usunięcie idealnych duplikatów
        self.df_invoices = self.df_invoices.drop_duplicates().reset_index(drop=True)
        self.df_invoices_lines = self.df_invoices_lines.drop_duplicates().reset_index(drop=True)
        bad_ids = set()

        # 2. Brak wpisów w fakturze
        ids_in_invoices = set(self.df_invoices['invoice_id'])
        ids_in_lines = set(self.df_invoices_lines['invoice_id'])

        missing_ids = ids_in_invoices - ids_in_lines
        for inv_id in missing_ids:
            self.invalid_invoices.append((
                inv_id, 'missing',
                f"Invoice with ID: {inv_id} has no corresponding line items in the invoice lines table."
            ))
        bad_ids.update(missing_ids)

        # 3. Duplikaty faktur z różnymi danymi
        dup_headers = self.df_invoices[self.df_invoices.duplicated(subset=['invoice_id'], keep=False)]
        dup_counts = dup_headers.groupby('invoice_id').size()  # liczba różnych wersji nagłówka

        header_ids = set(dup_counts.index) - bad_ids
        for inv_id in header_ids:
            self.invalid_invoices.append((
                inv_id, 'duplicate',
                'Duplicate invoices with inconsistent invoice data prevent unambiguous assignment of entries to a single invoice.'
            ))

        bad_ids.update(header_ids)

        # 4. Niezgodna liczba różnych wpisów faktur wśród duplikatów
        line_counts = self.df_invoices_lines.groupby(['invoice_id', 'line_no']).size()
        problematic = line_counts[line_counts > 1]

        structural_bad_ids = set()

        for group, count in problematic.items():
            if group[0] in bad_ids:
                continue

            structural_bad_ids.add(group[0])
            self.invalid_invoices.append((group[0], 'duplicate',
                                          'Duplicate line items with inconsistent  data prevent unambiguous assignment of entries to a single invoice.'
                                          ))

        bad_ids.update(structural_bad_ids)

        if bad_ids:
            self.df_invoices = self.df_invoices[~self.df_invoices['invoice_id'].isin(bad_ids)]
            self.df_invoices_lines = self.df_invoices_lines[~self.df_invoices_lines['invoice_id'].isin(bad_ids)]


    def build_invoices(self):
        inv_indexed = self.df_invoices.set_index("invoice_id")

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

            if invoice_id not in inv_indexed.index:
                self.invalid_invoices.append((invoice_id, 'missing', f"Found entries for invoice ID: {invoice_id} "
                                                                     f"but no matching invoice exists in the invoices table."))
                continue

            invoice_row = inv_indexed.loc[invoice_id]

            invoice = Invoice(
                invoice_id = invoice_id,
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


    def load_model(self):
        self.amount_outlier = AmountOutlier()
        self.amount_outlier.load("amount_outlier_model.pkl")


    def detect_anomalies(self):
        engine = BaseDetector(
            rules=[SumMismatch(), VatError()],
            batch_rules=[NearDuplicate(), self.amount_outlier]
        )

        types, details = engine.run(self.invoices)
        return types, details


    def create_predictions(self, types, details, output_path):
        rows = []

        for inv_id in types.keys():
            rows.append({
                "invoice_id": inv_id,
                "is_anomaly": int(len(types[inv_id]) > 0),
                "anomaly_types": ", ".join(types[inv_id]),
                "anomaly_details": "\n".join(details[inv_id])
            })

        if len(self.invalid_invoices) > 0:
            for inv_id, inv_type, inv_details in self.invalid_invoices:
                rows.append({
                    "invoice_id": inv_id,
                    "is_anomaly": 1,
                    "anomaly_types": inv_type,
                    "anomaly_details": inv_details
                })

        pred_details = pd.DataFrame(rows)

        if len(self.invalid_invoices) > 0:
            pred_details = pred_details.sort_values(by="invoice_id").reset_index(drop=True)

        pred = pred_details[["invoice_id", "is_anomaly", "anomaly_types"]]

        pred.to_csv(output_path, index=False)

        output_path = output_path.replace(".csv", "_with_details.csv")
        pred_details.to_csv(output_path, index=False)