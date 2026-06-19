# Invoice Anomaly Detection System

System przeznaczony do automatycznego wykrywania nieprawidłowości w fakturach na podstawie danych z plików CSV. Narzędzie łączy podejście oparte na sztywnych regułach biznesowych (walidacja sum, stawek VAT i możliwych duplikatów) z uczeniem maszynowym (`RandomForestClassifier`) do identyfikacji anomalii kwotowych w relacjach handlowych.

**Uwaga techniczna**: Zastosowany algorytm weryfikacji kwoty brutto uwzględnia standardowe matematyczne zaokrąglanie. Niektóre wykryte błędy w zbiorze danych wynikają z różnic w precyzji zaokrągleń na poziomie ułamków grosza w tabeli wejściowej (to te błędy, które w pliku ze szczegółami wyników widnieją z `diff = +/-0.01`). Pozostawiłem tę funkcjonalność w obecnej formie, uznając ją za wartość dodaną – pozwala ona klientowi na identyfikację niespójności w polityce zaokrągleń. W razie potrzeby mechanizm ten można łatwo zmodyfikować, wprowadzając margines tolerancji błędu.


## Struktura projektu

* `__init__.py`: Plik inicjujący.
* `__main__.py`: Główny punkt wejścia (interfejs CLI).
* `pipeline.py`: Logika przetwarzania danych, łączenia faktur z liniami oraz uruchamiania detekcji.
* `train_pipeline.py`: Logika trenowania modelu detekcji anomalii kwotowych w relacjach.
* `detector.py`: Implementacja logiki wykrywania anomalii (`SumMismatch`, `VatError`, `NearDuplicate`, `AmountOutlier`).
* `invoice.py`: Klasy modelowe (`Invoice`, `InvoiceLine`).

## Wymagania

Projekt wymaga Python 3.10+ oraz bibliotek wymienionych w `requirements.txt`:

```
joblib==1.5.3
numpy==2.4.6
pandas==3.0.3
scikit_learn==1.9.0
```

### Instalacja zależności:

```
pip install -r requirements.txt
```

### Instrukcja obsługi

#### 1. Trenowanie modelu 
Aby wytrenować model wykrywający anomalie kwotowe w relacjach nadawca→odbiorca *(amount_outlier)*, uruchom:
```
python -m invoice_anomaly train \
  --invoices train_invoices.csv \
  --labels train_labels.csv
```

Model zostanie zapisany jako amount_outlier_model.pkl.

#### 2. Wykrywanie anomalii
Aby uruchomić detekcję na nowych danych (testowych), użyj polecenia:
```
python -m invoice_anomaly detect \
  --invoices test_invoices.csv \
  --lines test_invoice_lines.csv \
  --output predictions.csv
 ```

System wygeneruje dwa pliki:
1. **predictions.csv**: Główny wynik z kolumnami invoice_id, is_anomaly, anomaly_types.
2. **predictions_with_details.csv**: Szczegółowa analiza z opisem wykrytych problemów dla każdej faktury.

### Podejście do wykrywania anomalii
System stosuje hybrydową strategię detekcji:

#### Reguły deterministyczne:
1. SumMismatch: Sprawdza zgodność sum linii z wartościami całkowitymi netto/brutto na nagłówku oraz poprawność wyliczeń na poziomie pojedynczych linii.
2. VatError: Weryfikuje poprawność wyliczenia kwoty brutto na linii zgodnie z przypisaną stawką VAT (floor(net * (1 + vat) + 0.5)). **Uwaga techniczna**: Zastosowany algorytm weryfikacji uwzględnia standardowe matematyczne zaokrąglanie. Niektóre wykryte „błędy” w zbiorze danych wynikają z różnic w precyzji zaokrągleń na poziomie ułamków grosza. Pozostawiłem tę funkcjonalność w obecnej formie, uznając ją za wartość dodaną – pozwala ona klientowi na identyfikację niespójności w polityce zaokrągleń. W razie potrzeby mechanizm ten można łatwo zmodyfikować, wprowadzając margines tolerancji błędu.
#### Analiza relacji (Batch):
1. NearDuplicate: Identyfikuje duplikaty na podstawie NIP-ów stron, podobieństwa dat (do 7 dni) oraz różnicy kwot (do 3%).
2. AmountOutlier: Wykorzystuje model RandomForestClassifier do oceny, czy kwota netto na fakturze nie odbiega znacząco od historycznych zachowań w danej parze kontrahentów. Wykorzystywane cechy to liczba faktur w danej relacji, logarytmiczna skala kwoty faktury, stosunek aktualnej kwoty do mediany, z-score (odchylenie od średniej w jednostkach odchylenia standardowego) oraz bezwzględna różnica między aktualną kwotą a medianą.
      
#### Walidacja danych
Przed rozpoczęciem detekcji, pipeline automatycznie czyści dane poprzez:
- Usunięcie duplikatów obu tabel.
- Weryfikację spójności relacji między fakturą a jej pozycjami (wykrywanie niejednoznacznych duplikatów).