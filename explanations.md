# Wytłumaczenie działania algorytmu na zbiorze testowym `test_invoices.csv` + `test_invoice_lines.csv`.

### Na zbiorze testowym wykryto 60 anomalii, z czego:
- amount_outlier → 12
- duplicate → 20
- sum_mismatch → 8
- vat_error → 20

W zbiorze nie wystąpiły współistniejące anomalie.

Do analizy przykładów skorzystałem z pliku `predictions_with_details.csv`, który zawiera szczegółowe informacje o wykrytych anomaliach.

#### Przykład 1. !

| invoice_id | is_anomaly | anomaly_types | anomaly_details                                                     |
|------------|------------|---------------|---------------------------------------------------------------------|
| TE-00021   | 1          | vat_error     | Line 1: vat_rate=0.23, expected=4196.15, actual=4196.14, diff=-0.01 |

Jest to przykład anomalii, która wynika ze zbyt słabej precyzji zaokrągleń na poziomie ułamków grosza w tabeli wejściowej.

```
(341.15 * 10) = 3411.50
(3411.50 * 1.23) = 4196,145 ~ 4196,15
```

#### Przykład 2.

| invoice_id | is_anomaly | anomaly_types | anomaly_details                                                      |
|------------|------------|---------------|----------------------------------------------------------------------|
| TE-00075   | 1          | vat_error     | Line 1: vat_rate=0.23, expected=13689.59, actual=13739.59, diff=50.0 |

Błąd wynika ze złej policzonej kwoty brutto dla pozycji nr 1 w fakturze o id TE-00075. Oczekiwana kwota powinna byc o 50 niższa od aktualnie widocznej na pozycji faktury.

#### Przykład 3.

| invoice_id | is_anomaly | anomaly_types | anomaly_details                                |
|------------|------------|---------------|------------------------------------------------|
| TE-00159   | 1          | sum_mismatch  | NET=7251.24, expected_sum=6251.24, diff=1000.0 |

Oczkiwana kwota netto dla faktury TE-00159 różni się od sum kwot netto dla pozycji owej faktury. Oczkiwana kwota netto powinna być o 1000 niższa.

#### Przykład 4.

| invoice_id   | is_anomaly | anomaly_types | anomaly_details              |
|--------------|------------|---------------|------------------------------|
| TE-00026     | 1          | duplicate     | Duplicated with TE-DUP-00026 |
| TE-DUP-00026 | 1          | duplicate     | Duplicated with TE-00026     |

Obie faktury są swoimi dublikatami. Mają te same NIP-y, różnica kwot jest mniejsza od 3% mniejszej wartości oraz różnica dat wystawienia obu faktur jest mniejsza od 7 dni.

#### Przykład 5.

| invoice_id | is_anomaly | anomaly_types  | anomaly_details                                                                                           |
|------------|------------|----------------|-----------------------------------------------------------------------------------------------------------|
| TE-00004   | 1          | amount_outlier | Almost certain anomaly (risk_score=0.997). Strong deviation from normal relation behavior.                |
| TE-00419   | 1          | amount_outlier | Very likely anomaly (risk_score=0.667). This transaction deviates from typical behavior in this relation. |

Model RandomForest zidentyfikował te transakcje jako odchylenia od typowej relacji nadawca→odbiorca. 
`risk_score` na poziomie 0.997 dla TE-00004 wskazuje na silną anomalię, podczas gdy `0.667` dla TE-00419 sugeruje zdarzenie wykraczające poza typowe ramy, ale o mniejszym stopniu pewności modelu.
Użytkownik otrzymuje zatem różne komunikaty w zależności od stopnia pewności, co pozwala na bardziej świadome podejmowanie decyzji o dalszych krokach.