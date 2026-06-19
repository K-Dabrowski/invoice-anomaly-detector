class Invoice:
    def __init__(self, invoice_id, invoice_date, invoice_number, sender_nip, recipient_nip, sender_name, recipient_name,
                 total_net, total_gross, currency, payment_due_date, risk_score, audit_passed, lines):
        self.invoice_id = invoice_id
        self.invoice_date = invoice_date
        self.invoice_number = invoice_number
        self.sender_nip = sender_nip
        self.recipient_nip = recipient_nip
        self.sender_name = sender_name
        self.recipient_name = recipient_name
        self.total_net = total_net
        self.total_gross = total_gross
        self.currency = currency
        self.payment_due_date = payment_due_date
        self.risk_score = risk_score
        self.audit_passed = audit_passed
        self.lines = lines

class InvoiceLine:
    def __init__(self, invoice_id, line_no, service_name, service_category,
                 quantity, unit_price_net, line_net, line_gross, vat_rate):
        self.invoice_id = invoice_id
        self.line_no = line_no
        self.service_name = service_name
        self.service_category = service_category
        self.quantity = quantity
        self.unit_price_net = unit_price_net
        self.line_net = line_net
        self.line_gross = line_gross
        self.vat_rate = vat_rate