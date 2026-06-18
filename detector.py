import pandas as pd
from itertools import combinations
from math import floor
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib


class BaseDetector:
    def __init__(self, rules, batch_rules):
        self.rules = rules
        self.batch_rules = batch_rules


    def run(self, invoices):
        per_invoice_result = {}
        per_invoice_details = {}

        for inv in invoices:
            anomaly_types = []
            anomaly_details = []

            for rule in self.rules:
                types, details = rule.detect(inv)
                anomaly_types.extend(types)
                anomaly_details.extend(details)

            per_invoice_result[inv.invoice_id] = anomaly_types
            per_invoice_details[inv.invoice_id] = anomaly_details

        batch_result = {}
        batch_details = {}

        for batch_rule in self.batch_rules:
            types, details = batch_rule.detect(invoices)
            for inv_id, t in types.items():
                batch_result.setdefault(inv_id, []).extend(t)
            for inv_id, d in details.items():
                batch_details.setdefault(inv_id, []).extend(d)

        merged_types, merged_details = self._merge_results(per_invoice_result, per_invoice_details, batch_result, batch_details)
        return merged_types, merged_details


    def _merge_results(self, per_invoice_result, per_invoice_details, batch_result, batch_details):
        merged_types = {}
        merged_details = {}

        for inv_id in per_invoice_result:
            merged_types[inv_id] = per_invoice_result.get(inv_id, []) + batch_result.get(inv_id, [])
            merged_details[inv_id] = per_invoice_details.get(inv_id, []) + batch_details.get(inv_id, [])

        return merged_types, merged_details


class SumMismatch():
    def detect(self, invoice):
        anomaly_types = []
        anomaly_details = []

        net_expected = sum(x.line_net for x in invoice.lines)

        if invoice.total_net != net_expected:
            anomaly_types.append("sum_mismatch")
            anomaly_details.append(f"NET={invoice.total_net/100}, expected_sum={net_expected/100}, diff={(invoice.total_net - net_expected)/100}")

        gross_expected = sum(x.line_gross for x in invoice.lines)

        if invoice.total_gross != gross_expected:
            anomaly_types.append("sum_mismatch")
            anomaly_details.append(f"GROSS={invoice.total_gross/100}, expected_sum={gross_expected/100}, "
                                   f"diff={(invoice.total_gross - gross_expected)/100}")

        for line in invoice.lines:
            line_expected = line.quantity * line.unit_price_net

            if line_expected != line.line_net:
                anomaly_types.append(f"sum_mismatch")
                anomaly_details.append(f"Line {line.line_no}: quantity={line.quantity}, unit_price_net={line.unit_price_net/100}, "
                                       f"expected={line_expected/100}, actual={line.line_net/100}, diff={(line.line_net - line_expected)/100}")

        return anomaly_types, anomaly_details


class VatError():
    def detect(self, invoice):
        anomaly_types = []
        anomaly_details = []

        for line in invoice.lines:
            expected = floor(line.line_net * (1 + line.vat_rate) + 0.5)

            if line.line_gross != expected:
                anomaly_types.append(f"vat_error")
                anomaly_details.append(f"Line {line.line_no}: vat_rate={line.vat_rate}, expected={expected/100}, "
                                       f"actual={line.line_gross/100}, diff={(line.line_gross - expected)/100}")

        return anomaly_types, anomaly_details


class NearDuplicate():
    def detect(self, invoices):
        grouped = {}

        for inv in invoices:
            nips = (inv.sender_nip, inv.recipient_nip)
            grouped.setdefault(nips, []).append(inv)

        duplicated_invoices = {}

        for nips, inv_list in grouped.items():
            if len(inv_list) > 1:
                for inv1, inv2 in combinations(inv_list, 2):
                    min_gross = min(inv1.total_gross, inv2.total_gross)
                    max_gross = max(inv1.total_gross, inv2.total_gross)
                    if abs(max_gross - min_gross) < (min_gross * 0.03):
                        if abs((inv2.invoice_date - inv1.invoice_date).days) <= 7:
                            duplicated_invoices.setdefault(inv1.invoice_id, set()).add(inv2.invoice_id)
                            duplicated_invoices.setdefault(inv2.invoice_id, set()).add(inv1.invoice_id)

        anomaly_types = {
            inv_id: ["duplicate"]
            for inv_id in duplicated_invoices.keys()
        }

        anomaly_details = {
            inv_id: [f"Duplicated with {', '.join(sorted(list(dups)))}"]
            for inv_id, dups in duplicated_invoices.items()
        }

        return anomaly_types, anomaly_details


class AmountOutlier:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=300,
            max_depth=10,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )
        self.fitted = False


    def load(self, path):
        self.model = joblib.load(path)
        self.fitted = True


    def build_features(self, invoices):
        grouped = {}

        for inv in invoices:
            key = (inv.sender_name, inv.recipient_name)
            grouped.setdefault(key, []).append(inv.total_net)

        X = []
        ids = []

        for inv in invoices:
            key = (inv.sender_name, inv.recipient_name)

            values = grouped[key]

            current = inv.total_net

            median = np.median(values) if len(values) > 0 else current
            mean = np.mean(values) if len(values) > 0 else current
            std = np.std(values) + 1e-9

            ratio = current / (median + 1e-9)
            z = (current - mean) / std
            diff = current - median

            X.append([
                len(values),
                np.log1p(current),
                ratio,
                z,
                diff
            ])

            ids.append(inv.invoice_id)

        return np.array(X), ids


    def fit(self, invoices, labels):
        X, ids = self.build_features(invoices)
        y = np.array([labels.get(i, 0) for i in ids])

        self.model.fit(X, y)
        self.fitted = True

        joblib.dump(self.model, "amount_outlier_model.pkl")

    def detect(self, invoices):
        if not self.fitted:
            raise Exception("Model not fitted")

        X, ids = self.build_features(invoices)
        probs = self.model.predict_proba(X)[:, 1]

        anomaly_types = {}
        anomaly_details = {}

        for inv_id, p in zip(ids, probs):
            if p > 0.6:
                anomaly_types[inv_id] = ["amount_outlier"]
                if p < 0.8:
                    anomaly_details[inv_id] = [f"Very likely anomaly (risk_score={p:.3f}). This transaction deviates from typical behavior in this relation."]
                else:
                    anomaly_details[inv_id] = [f"Almost certain anomaly (risk_score={p:.3f}). Strong deviation from normal relation behavior."]

        return anomaly_types, anomaly_details