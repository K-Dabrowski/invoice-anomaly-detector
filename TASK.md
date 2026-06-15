# Zadanie rekrutacyjne: wykrywanie anomalii na fakturach

## Cel

Zbuduj program w Pythonie, który wykrywa podejrzane faktury w danych CSV.

## Pliki z danymi

Dostajesz **8 plików CSV** (bez podkatalogów):

| Plik | Opis |
|------|------|
| `train_invoices.csv` | faktury — zestaw treningowy |
| `train_invoice_lines.csv` | pozycje faktur — trening |
| `train_labels.csv` | etykiety (0/1) — trening |
| `val_invoices.csv` | faktury — walidacja |
| `val_invoice_lines.csv` | pozycje — walidacja |
| `val_labels.csv` | etykiety — walidacja |
| `test_invoices.csv` | faktury — test (**bez etykiet**) |
| `test_invoice_lines.csv` | pozycje — test |

### Kolumny w `*_invoices.csv`
- `invoice_id`, `invoice_date`, `invoice_number`
- `sender_nip`, `recipient_nip`, `sender_name`, `recipient_name`
- `total_net`, `total_gross`, `currency`, `payment_due_date`
- `risk_score`, `audit_passed`

### Kolumny w `*_invoice_lines.csv`
- `invoice_id`, `line_no`, `service_name`, `service_category`
- `quantity`, `unit_price_net`, `line_net`, `line_gross`, `vat_rate`

### Kolumny w `*_labels.csv` (train + val)
- `invoice_id`, `is_anomaly` (0/1), `anomaly_types`

## Co wykrywać

W danych występują (osobno lub łącznie) co najmniej takie anomalie:

1. **sum_mismatch** — suma pozycji nie zgadza się z totalami na fakturze
2. **vat_error** — brutto ≠ netto × (1 + stawka VAT) na pozycji
3. **duplicate** — duplikat / near-duplikat (te same NIP-y, kwoty, bliska data)
4. **amount_outlier** — kwota nietypowa jak na relację nadawca→odbiorca

Część da się złapać regułami, część statystyką / modelem ML (`scikit-learn`).

## Wymagania techniczne

- Python 3.10+
- `pandas`, `numpy`, `scikit-learn`
- **Programowanie obiektowe** — minimum:
  - klasa reprezentująca fakturę (np. `Invoice`)
  - klasa (lub interfejs) detektora anomalii (np. `BaseDetector` + konkretne implementacje)
  - klasa spinająca pipeline (np. `AnomalyPipeline`)
- Uruchamianie z shella, bez GUI
- Własne repo + `requirements.txt` + **README** z instrukcją uruchomienia

## Sugerowany interfejs CLI

```bash
pip install -r requirements.txt

python -m invoice_anomaly detect \
  --invoices test_invoices.csv \
  --lines test_invoice_lines.csv \
  --output predictions.csv
```

Plik `predictions.csv`:
```csv
invoice_id,is_anomaly
TE-00001,0
TE-00002,1
```

Opcjonalnie kolumna `anomaly_types` (np. `sum_mismatch,vat_error`).

## Co oddajesz

1. Link do repo (**minimum 3 commity** w historii — nie jeden wielki dump na koniec)
2. Krótki opis podejścia (w README wystarczy)
3. `predictions.csv` wygenerowany na `test_invoices.csv` + `test_invoice_lines.csv`
4. `explanations.md` — dla **5 faktur oznaczonych jako anomalia** w `predictions.csv` napisz: **dlaczego** uznałeś je za podejrzane i **jaki typ problemu** widzisz w danych (np. błąd VAT, zła suma, duplikat itd.)

## Na co patrzymy

- Czy kod w ogóle działa
- Czy używasz pandas / sklearn tam, gdzie ma to sens
- Czy potrafisz uzasadnić wykrycia (nie tylko wypluć 0/1)
- Jakość kodu: nazwy, podział na moduły, brak spaghetti w jednym pliku

Powodzenia!
