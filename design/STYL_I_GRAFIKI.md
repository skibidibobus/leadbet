# Styl Wizualny (60-30-10) i Katalog Grafik — Platforma Analiz Kursów Bukmacherskich

> **Koncepcja wizualna:** *„Quant Slate & Emerald Terminal”* — estetyka instytucjonalnej analityki finansowej (fintech / quant trading) przeniesiona na analizę sportową. Świadomie odrzuca agresywne, jaskrawe „kasynowe” neony na rzecz czytelności długich sesji z tabelami kursów, rozkładami prawdopodobieństwa i kalkulacją wartości oczekiwanej (`+EV`).

---

## 1. System Kolorystyczny 60-30-10 (Zbadany i Zoptymalizowany pod WCAG 2.2)

Dlaczego **Dark Mode jako motyw główny** (z opcjonalnym wariantem Light)?
Użytkownicy analizujący kursy spędzają długie minuty na skanowaniu gęstych tabel liczbowych i wykresów rozkładu prawdopodobieństwa. Głęboki grafitowo-granatowy łupek (`#0B0F19`, bez czystej czerni `#000000`, która powoduje tzw. *halation* / rozlewanie się białego tekstu) minimalizuje zmęczenie oczu i podnosi postrzeganą precyzję danych matematycznych.

### Rozkład proporcji powierzchni (Budżet Pikseli)

| Warstwa | Udział | Nazwa Tokenu | HEX | RGB | Zastosowanie na stronie |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **Dominujący** | **60%** | `canvas-obsidian` | `#0B0F19` | `11, 15, 25` | Główne tło aplikacji, marginesy, przestrzeń oddechu wokół tabel |
| Dominujący (siatka) | *(w 60%)* | `canvas-midnight` | `#0F1624` | `15, 22, 36` | Zagnieżdżone wiersze kalkulacji, podkłady wykresów, tło pod-nagłówków |
| **Strukturalny** | **30%** | `surface-slate` | `#131C2E` | `19, 28, 46` | Karty meczów, panele boczne generatora kuponu, nawigacja górna |
| Strukturalny (elewacja) | *(w 30%)* | `surface-elevated` | `#1B263B` | `27, 38, 59` | Nagłówki tabel, stany hover, aktywne moduły kuponu, modale |
| Strukturalny (ramki) | *(w 30%)* | `border-hairline` | `#23324D` | `35, 50, 77` | Cienkie linie 1px oddzielające kontenery (hierarchia przez elewację zamiast cieni) |
| Strukturalny (dane) | *(w 30%)* | `quant-teal` | `#0D9488` / `#047857` | `13, 148, 136` | Słupki rozkładu Poissona, linie trendu kursów, strefy tła dla filtrów |
| **Akcent (Focal)** | **10%** | `signal-emerald` | `#10B981` | `16, 185, 129` | Dodatnie `+EV`, aktywna kategoria sportowa, krzywa prawdopodobieństwa wejścia |
| Akcent (CTA / Edge) | *(w 10%)* | `alpha-amber` | `#F59E0B` | `245, 158, 11` | Wyłącznie główny przycisk `GENERUJ KUPON`, top-edge alerty i oznaczenie lig wysokiej wariancji (np. Tenis stołowy) |

### Kolory Typografii i Semantyczne Stany Pomocnicze (WCAG 2.2 AA/AAA)

* **Tekst główny (`text-primary`):** `#F8FAFC` (kontrast na `#0B0F19` > `15:1` — WCAG AAA).
* **Tekst tabelaryczny (`text-secondary`):** `#CBD5E1` (kontrast na `#131C2E` > `9:1` — czytelny dla ułamków i kursów).
* **Etykiety pomocnicze (`text-muted`):** `#94A3B8` (kontrast na `#0B0F19` > `6.5:1` — WCAG AA).
* **Ujemne EV / Wysoka marża (`semantic-loss`):** `#F87171` (zmiękczona czerwień dla dark mode; **nigdy sam kolor** — zawsze w parze ze znakiem `-`, strzałką `▼` lub etykietą `Wysoka marża`).
* **Ostrzeżenie wariancji (`semantic-warn`):** `#FBBF24` (używane np. przy wysokim współczynniku volatility $\sigma$ w tenisie stołowym).

### Opcjonalny Tryb Jasny (Tokeny 60-30-10 na przyszły przełącznik motywu)
* **60% Tło:** `#F8FAFC` (Soft Cool Off-White — brak oślepiającego `#FFFFFF` na dużych obszarach)
* **30% Kontenery:** `#FFFFFF` z obramowaniem `#E2E8F0` i słupkami `#0D9488`
* **10% Akcent:** `#059669` (Emerald 600) i `#D97706` (Amber 600) dla zachowania kontrastu $\ge 4.5:1$ na jasnym tle.

---

## 2. Typografia i Reguły Czytelności Liczbowej

1. **Nagłówki i nawigacja:** `Plus Jakarta Sans` lub `Inter` (wagi 500, 600, 700, 800; ciasny tracking `-0.02em` na dużych nagłówkach).
2. **Wszystkie kursy, procenty i metryki matematyczne:** `JetBrains Mono` (lub `Inter` z wymuszonym `font-variant-numeric: tabular-nums`), aby kolumny typu `1.82`, `61.4%`, `+4.8%` zawsze były wyrównane co do piksela w pionie.
3. **Zasada „Never Color Alone”:** Każda zmiana kursu i każda wartość EV musi nieść znak (`+` / `-`), kierunek (`▲` / `▼`) oraz wartość liczbową, aby użytkownicy z daltonizmem (deuteranopia/protanopia) odczytywali dane bezbłędnie.

---

## 3. Pełny Katalog Grafik Wymaganych na Stronie

Poniżej znajduje się zestawienie wszystkich zasobów graficznych, które muszą powstać dla platformy — wraz z rolą, proporcją 60-30-10 oraz wskazaniem przykładów wygenerowanych w folderze [`examples/`](file:///Users/hubertlichorobiec/Antigravity%20projects/bukmacherka/design/examples).

### A. Grafika Hero / Sekcja Metodologii (`hero-quant-analytics` + `hero-swiss-editorial`)
* **Gdzie na stronie:** Strona główna (tło sekcji Hero + kompozycja komponentów nad złożeniem) oraz podstrona `/metodologia`.
* **Zasada Anty-Slop (Krytyczna reguła artystyczna):** Kategoryczny zakaz generowania generycznych „świecących hologramów 3D”, neonowych siatek sci-fi, rozmytej mgły i losowych świecących kropek. Wszystkie grafiki Hero mają mieć charakter **matowej, taktylnej architektury sportowej** lub **płaskiego szwajcarskiego designu edytorialowego (2D Swiss Print)** — z ostrymi krawędziami i wysoką czytelnością pod białą typografię.
* **Wybrany wariant główny (ustalony w `/grill-me`):** Połączenie taktylnego zdjęcia kortu w tle ([hero-quant-analytics.jpg](file:///Users/hubertlichorobiec/Antigravity%20projects/bukmacherka/design/examples/hero-quant-analytics.jpg)) z czystymi, interaktywnymi kartami matematycznymi React/SVG na pierwszym planie ([hero-quant-analytics.svg](file:///Users/hubertlichorobiec/Antigravity%20projects/bukmacherka/design/examples/hero-quant-analytics.svg)).
* **Wariant dodatkowy (podstrona `/metodologia`):** Płaski szwajcarski plakat 2D łączący rzut boiska z histogramem rozkładu i geometrią kortów bez efektów glow ([hero-swiss-editorial.jpg](file:///Users/hubertlichorobiec/Antigravity%20projects/bukmacherka/design/examples/hero-swiss-editorial.jpg)).
* **Zastosowanie 60-30-10:** 60% matowego obsydianu `#0B0F19`, 30% strukturalnych powierzchni `#131C2E` i linii `#047857`, 10% precyzyjnych punktów `#10B981` i pojedynczego akcentu `#F59E0B`.

### B. Koncept Głównego Widoku Dashboardu i Kalkulatora (`dashboard-ui-koncept` + `dashboard-ui-wireframe`)
* **Gdzie na stronie:** Główny ekran roboczy aplikacji (`/analiza` oraz `/generator-kuponow`).
* **Opis wizualny:** Trójkolumnowy układ analityczny:
  1. Pasek górny z aktywnymi w v1 kategoriami sportowymi (**Piłka nożna, Koszykówka, Tenis ziemny, Hokej**) i selektorem legalnego bukmachera PL (`0.88×` vs promocje bez podatku).
  2. Główna tabela wartości matematycznej (`Kurs referencyjny`, `Kurs PL (edytowalny)`, `P(model)`, `Marża`, `EV Netto`).
  3. Panel wykresu rozkładu wyników (macierz Poissona / krzywa Markowa / Skellama) z metrykami faktycznymi (`xG`, `Brier Score`, `Kelly`).
  4. Prawy panel „Generator Kuponu” maksymalizujący szansę wejścia $P(\text{kupon})$ w zadanym przedziale kursu, z jawnym przelicznikiem podatku `0.88×`, możliwością nadpisania kursu PL w 1 kliknięciu oraz przyciskiem CTA `#F59E0B`.
* **Przykłady w repozytorium:**
  * Wersja koncepcyjna UI (raster): [dashboard-ui-koncept.jpg](file:///Users/hubertlichorobiec/Antigravity%20projects/bukmacherka/design/examples/dashboard-ui-koncept.jpg)
  * Precyzyjny wireframe SVG z polską terminologią i liczbami: [dashboard-ui-wireframe.svg](file:///Users/hubertlichorobiec/Antigravity%20projects/bukmacherka/design/examples/dashboard-ui-wireframe.svg)

### C. System Ikon i Kafelków Kategorii Sportowych (`kafelki-sportowe-koncept` + `ikony-kategorii-sportowych`)
* **Gdzie na stronie:** Pasek nawigacji dyscyplin, karty wyboru kategorii w Generatorze Kuponów, nagłówki ligowe.
* **Lista dyscyplin w systemie (4 aktywne w v1 + 2 przygotowane pod Fazę 2):**
  1. **Piłka nożna (v1)** — siatka sześciokątna piłki + stożek kąta strzału (`xG`).
  2. **Koszykówka (v1)** — geometria piłki + krzywa paraboliczna rzutu i linia trumny.
  3. **Tenis ziemny (v1)** — szew piłki + linie końcowe kortu i punkty odbicia (`serve/return`).
  4. **Hokej na lodzie (v1)** — krążek + pole bramkowe i wektory prędkości.
  5. *Siatkówka (Faza 2 — ukryta w v1)* — siatka boiska + wektor wybicia ponad siatkę.
  6. *Tenis stołowy (Faza 2 — ukryta w v1)* — rakietka + piłeczka w pętli rotacyjnej nad siatką stołu (wyróżnik `#F59E0B` dla wysokiej zmienności / modelu Glicko-2).
* **Przykłady w repozytorium:**
  * Arkusz koncepcyjny kafelków 3×2 (raster): [kafelki-sportowe-koncept.jpg](file:///Users/hubertlichorobiec/Antigravity%20projects/bukmacherka/design/examples/kafelki-sportowe-koncept.jpg)
  * Produkcjyjny arkusz wektorowy SVG: [ikony-kategorii-sportowych.svg](file:///Users/hubertlichorobiec/Antigravity%20projects/bukmacherka/design/examples/ikony-kategorii-sportowych.svg)

### D. Karta Wygenerowanego Kuponu Matematycznego (`karta-kuponu-matematycznego`)
* **Gdzie na stronie:** Wynik pracy Generatora Kuponów, historia symulacji, widok udostępniania (link / eksport PNG).
* **Opis wizualny:** Strukturalna karta dzieląca każdą nogę kuponu na: kategorię sportową, nazwę algorytmu (np. `Dixon-Coles`, `Markov Bo5`), prawdopodobieństwo modelu vs prawdopodobieństwo rynkowe bez marży, oraz dolną sekcję finansowo-podatkową (`Kurs brutto`, `Podatek 0.88×`, `Szansa wejścia %`, `Wygrana netto PLN`, `Próg 2280 PLN`, `Kelly`).
* **Przykład w repozytorium:** [karta-kuponu-matematycznego.svg](file:///Users/hubertlichorobiec/Antigravity%20projects/bukmacherka/design/examples/karta-kuponu-matematycznego.svg)

### E. Specyfikacja Palety 60-30-10 (`paleta-60-30-10-system`)
* **Gdzie w projekcie:** Dokumentacja dla zespołu UI (model Argon) i weryfikacja wizualna tokenów CSS.
* **Przykład w repozytorium:** [paleta-60-30-10-system.svg](file:///Users/hubertlichorobiec/Antigravity%20projects/bukmacherka/design/examples/paleta-60-30-10-system.svg)

### F. Dodatkowe Grafiki Produkcyjne do Zaprojektowania podczas Implementacji (Faza UI)
1. **Wykresy Data-Viz (biblioteka Recharts / ECharts w tokenach 60-30-10):**
   * *Heatmapa dokładnych wyników (Piłka nożna 0:0 – 4:4)* — skala od `#131C2E` (niskie P) przez `#047857` do `#10B981` (najwyższe P).
   * *Krzywa kalibracji modelu (Reliability Diagram)* — linia idealna $y=x$ przerywana `#94A3B8`, krzywa historycznej skuteczności `#10B981`.
   * *Wykres ruchu kursów i CLV (Closing Line Value)* — linia bukmachera `#CBD5E1` vs Fair Line `#10B981`.
2. **Odznaki Statusu Prawnego i Podatkowego (SVG 20×20px):**
   * Tarcza `Licencja MF PL` (`#10B981`), znacznik `0.88× Standard` (`#94A3B8`), znacznik `Bez Podatku 1.00×` (`#F59E0B`), ikona ostrzegawcza `18+ Odpowiedzialna Gra` w stopce.
3. **Ilustracje Stanów Pustych (Empty States):**
   * Minimalistyczna grafika „Brak zdarzeń z dodatnim EV dla wybranych filtrów” (zarys pustego wykresu w `#23324D` i akcentem `#F59E0B` z sugestią poszerzenia kategorii).
