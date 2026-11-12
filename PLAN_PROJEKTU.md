# Szczegółowy Plan Projektu: Platforma Matematycznej Analizy Kursów Bukmacherskich i Generatora Kuponów („QUANTKUPON”)

> **Charakter systemu:** Czysto matematyczno-faktowy system analityczny (**budżet 0 zł** poza Google AI Pro, analiza wyłącznie **przedmeczowa *pre-match***). Każda ocena zdarzenia i każdy proponowany kupon wynikają bezpośrednio z modeli probabilistycznych, usunięcia marży bukmachera (*de-vigging*), estymacji wartości oczekiwanej (`EV`) z uwzględnieniem polskiego prawa podatkowego oraz optymalizacji dopasowanej do personalizacji użytkownika.

### Decyzje Produktowe i Architektoniczne (Uzgodnione w `/grill-me`)
* **Zakres dyscyplin w v1 (4 aktywne kategorie):** W wersji v1 w interfejsie pokazujemy wyłącznie **4 dyscypliny z realnymi, darmowymi danymi**: **Piłka nożna (TOP5)**, **Koszykówka (NBA)**, **Tenis ziemny (ATP/WTA)** oraz **Hokej (NHL)**. **Siatkówka** i **Tenis stołowy** zostają ukryte w UI v1 (za flagą `ENABLE_PHASE2_SPORTS=false`) i wrócą w Fazie 2 po podłączeniu płatnego feedu lub umowy partnerskiej.
* **Tryb 0 zł Pre-Match + Hybrydowy Kalkulator Kursów PL:** Dane aktualizują się **2× dziennie** z darmowych limitów API (*The Odds API* / *OddsPapi* + otwarte statystyki) przez harmonogram **GitHub Actions** i trafiają do bazy **Neon PostgreSQL**. Generator buduje kupon na bazie $P(\text{model})$ i kursu referencyjnego (*Fair Odds*) / estymowanego kursu PL, a użytkownik może **1 kliknięciem nadpisać kurs dowolnego meczu** tym ze swojego bukmachera (`Betclic` / `Fortuna` / `STS`) z natychmiastowym przeliczeniem `EV` i `0.88×`.
* **Cel Generatora Kuponów:** Domyślnie **maksymalizuje szansę matematyczną wejścia $P(\text{kupon})$** w zadanym przez użytkownika przedziale kursu (bez blokowania przy ujemnym EV podatkowym), przy **jawnym wyświetlaniu dokładnego `EV Netto`** (oraz opcjonalnym filtrem `Tylko +EV`).
* **Konta i Historia:** Logowanie od dnia 1 (**Auth.js / NextAuth**: Google OAuth + e-mail) wpięte w **Neon PostgreSQL**, zapisywanie kuponów użytkownika oraz pełna zgodność **RODO i 18+**.
* **Hosting 0 zł (gotowy pod przyszłą afiliację):** Frontend **Next.js na Cloudflare Pages** (dozwolony użytek komercyjny za 0 zł) + baza **Neon PostgreSQL** (1 GB, bez kasowania po 30 dniach) + **Render Free (FastAPI)** dla dynamicznej optymalizacji kuponów (z akceptacją ~1 min wybudzania po 15 min bezczynności, podczas gdy przeliczone tabele meczowe mogą ładować się błyskawicznie przez SSR/Neon) + ciężkie przeliczenia modeli `2×/dzień` w **GitHub Actions**.
* **Styl Hero:** Połączenie taktylnego zdjęcia kortu w tle ([hero-quant-analytics.jpg](file:///Users/hubertlichorobiec/Antigravity%20projects/bukmacherka/design/examples/hero-quant-analytics.jpg)) z czystymi, interaktywnymi kartami matematycznymi React/SVG na pierwszym planie ([hero-quant-analytics.svg](file:///Users/hubertlichorobiec/Antigravity%20projects/bukmacherka/design/examples/hero-quant-analytics.svg)).

---

## Spis Treści
1. [Architektura Strony Internetowej, UX i Podział na Kategorie](#1-architektura-strony-internetowej-ux-i-podział-na-kategorie)
2. [Połączenie z Legalnym Bukmacherem w Polsce i Silnik Podatkowy](#2-połączenie-z-legalnym-bukmacherem-w-polsce-i-silnik-podatkowy)
3. [Silnik Matematyczny i Algorytmy (Krok po Kroku)](#3-silnik-matematyczny-i-algorytmy-krok-po-kroku)
4. [Algorytm Generatora i Personalizacji Kuponów](#4-algorytm-generatora-i-personalizacji-kuponów)
5. [Stack Technologiczny, Baza Danych i Kontrakty API](#5-stack-technologiczny-baza-danych-i-kontrakty-api)
6. [Styl Wizualny (60-30-10) i Grafiki](#6-styl-wizualny-60-30-10-i-grafiki)
7. [Szczegółowy Podział Pracy na Modele: Gemini 4 Hydrogen vs Gemini 4 Argon](#7-szczegółowy-podział-pracy-na-modele-hydrogen-vs-argon)
8. [Zgodność Prawna w Polsce (Compliance 18+)](#8-zgodność-prawna-w-polsce-compliance-18)

---

## 1. Architektura Strony Internetowej, UX i Podział na Kategorie

### 1.1 Mapa Podstron (App Routes)
* **`/` (Dashboard Przeglądowy + Hero Metodologii):** Najwyższe matematyczne okazje (`Top +EV`) z wszystkich dyscyplin, podsumowanie kalibracji modeli (Brier Score, historyczne CLV) oraz szybkie wejście do kategorii sportowych.
* **`/analiza/[sport]` (Widok Kategorii Sportowej):** Lista nadchodzących zdarzeń podzielona na ligi/turnieje z tabelą: Kurs bukmachera, Prawdopodobieństwo bez marży (`p_fair`), Prawdopodobieństwo modelu (`p_model`), Marża bukmachera (`vig %`), Edge (`EV Netto %`) oraz próg bezpieczeństwa / wariancji.
* **`/mecz/[id]` (Karta Analityczna Zdarzenia):** Szczegółowe rozbicie matematyczne (np. macierz dokładnych wyników Poissona dla piłki nożnej lub symulacja punkt-po-punkcie Markowa dla tenisa/tenisa stołowego), wykres ruchu kursów, wskaźniki formy/Elo/Glicko-2 i uzasadnienie faktograficzne w punktach.
* **`/generator-kuponow` (Personalizowany Kreator Kuponów):** Interaktywny panel, w którym użytkownik określa swoje parametry (kategorie, rynki, profil ryzyka, docelowy kurs lub minimalną szansę wejścia, liczbę zdarzeń, stawkę i bukmachera), a algorytm konstruuje matematycznie optymalne kupony z pełnym wyliczeniem kursu brutto, kursu netto po podatku oraz prawdopodobieństwa trafienia całego kuponu.
* **`/backtest-i-kalibracja` (Audyt Matematyczny):** Transparentny raport dokładności algorytmów na danych historycznych: krzywa kalibracji (*Reliability Diagram*), średni *Brier Score*, *Log-Loss* oraz *Closing Line Value (CLV)*.
* **`/metodologia`:** Opis wzorów (Dixon-Coles, Shin, Glicko-2, Markov, Kelly, podatek PL 12%/10%) w przystępnej formie dla użytkownika.

### 1.2 Hierarchia Kategorii Sportowych i Rynkowych (Wersja v1 vs Faza 2)

W **v1 (0 zł)** w nawigacji i generatorze widoczne są wyłącznie pierwsze 4 dyscypliny z automatycznym zasilaniem statystycznym. Pozostałe 2 czekają w silniku matematycznym na Fazę 2 (po uruchomieniu komercyjnego feedu / partnerstwa):

| Status | Kategoria główna | Podkategorie ligowe / rozgrywkowe | Obsługiwane rynki (Markets) | Darmowe źródła danych (v1) |
| :--- | :--- | :--- | :--- | :--- |
| **v1 (Aktywna)** | **1. Piłka nożna** | Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Liga Mistrzów | `1X2`, `Podwójna szansa`, `Over/Under goli (1.5 / 2.5 / 3.5)`, `BTTS`, `Handicap azjatycki` | `football-data.org`, `football-data.co.uk`, `The Odds API` |
| **v1 (Aktywna)** | **2. Koszykówka** | NBA | `Zwycięzca (ML z dogrywką)`, `Handicap punktowy (Spread)`, `Suma punktów (O/U)` | `nba_api`, `The Odds API` |
| **v1 (Aktywna)** | **3. Tenis ziemny** | ATP Tour, WTA Tour (podział: `Hard`, `Clay`, `Grass`) | `Zwycięzca meczu`, `Handicap setowy`, `Over/Under gemów` | Archiwa `tennis-data.co.uk` / Sackmann (`CC BY-NC-SA 4.0`), `The Odds API` |
| **v1 (Aktywna)** | **4. Hokej na lodzie** | NHL | `1X2 (60')`, `Zwycięzca z OT/SO (ML)`, `Over/Under bramek (5.5)`, `Handicap -1.5` | Oficjalne statystyki NHL API, `The Odds API` |
| *Faza 2 (Ukryta)* | *5. Siatkówka* | *PlusLiga, Tauron Liga, Liga Mistrzów CEV, Liga Narodów* | *`Zwycięzca`, `Handicap setowy (-1.5 / +1.5)`, `O/U setów`* | *Wymaga komercyjnego feedu* |
| *Faza 2 (Ukryta)* | *6. Tenis stołowy* | *WTT Series, TT Elite Series, Setka Cup, Liga Pro (`Bo5` / `Bo7`)* | *`Zwycięzca`, `Handicap setowy (-1.5 / +1.5)`, `Suma punktów`* | *Wymaga płatnego feedu / `Glicko-2 Volatility Guard`* |

---

## 2. Połączenie z Legalnym Bukmacherem w Polsce i Silnik Podatkowy

### 2.1 Realia Rynkowe Legalnych Bukmacherów (Licencja Ministerstwa Finansów RP) i Tryb Hybrydowy 0 zł
W Polsce legalne zakłady internetowe mogą prowadzić wyłącznie operatorzy z aktualną licencją Ministra Finansów (m.in. **Betclic, Superbet, Fortuna, STS, LV BET, Betfan, Etoto, forBET**).
* **Fakt techniczny:** Polscy bukmacherzy **nie udostępniają otwartych, darmowych i oficjalnych API REST/JSON** dla osób trzecich.
* **Rozwiązanie architektoniczne w v1 (0 zł — Tryb Hybrydowy Pre-Match):**
  1. **Harmonogram 2× dziennie (GitHub Actions Cron -> Neon PostgreSQL):** Z darmowych limitów agregatorów (**The Odds API**: 500 kredytów/mies.; opcjonalnie **OddsPapi**: 250 zapytań/mies.) pobieramy wyłącznie oferty **przedmeczowe** dla wybranych 4–5 lig/turniejów (budżet ok. 8 pobrań dziennie), aby **nie przekroczyć planu 0 zł**.
  2. **Tryb Hybrydowy w Kalkulatorze i Generatorze:** System wylicza bezmarżową szansę prawdziwą $p_{\text{true}}$, *Fair Odds* oraz estymowany kurs rynkowy PL, a na karcie kuponu każde zdarzenie posiada edytowalne pole **„Kurs u Twojego bukmachera (STS/Fortuna/Betclic)”**. Wpisanie kursu z aplikacji bukmachera natychmiast przelicza `EV Netto`, podatek `0.88×` i wypłatę.
  3. **Wzorzec Adaptera (`BookmakerFeedAdapter` — gotowy na Fazę 2):** Oddziela logikę matematyczną od źródła danych, pozwalając w przyszłości bez zmiany silnika przełączyć się na płatny polski agregator (np. **ArbiScan**) lub oficjalny feed XML/JSON z programu partnerskiego.

### 2.2 Polski Silnik Podatkowy (`PolishTaxEngine`)
Każda kalkulacja kursu rzeczywistego, wartości oczekiwanej `EV` oraz wypłaty na kuponie musi dokładnie odzwierciedlać polskie przepisy i warunki promocji wybranych operatorów:

1. **Standardowy podatek od gry (12% obrotowy):**
   $$\text{Stawka w grze} = S \times 0.88$$
   $$\text{Kurs realny netto} = O_{\text{brutto}} \times 0.88$$
   Próg rentowności (*break-even*) wzrasta z $\frac{1}{O}$ aż do $\frac{1}{0.88 \cdot O}$ (np. dla kursu `2.00` potrzebna skuteczność rośnie z `50.0%` do `56.82%`!).

2. **Moduł Reguł Promocji „Bez Podatku” (parametryzowane profile bukmacherów):**
   * **Betclic („Bez Podatku 2.0”):** $k_{\text{tax}} = 1.00$ dla kuponów AKO spełniających warunek $\ge 2$ zdarzenia o kursie minimalnym każdego zdarzenia $\ge 1.20$ (oraz SOLO w ramach limitu regulaminowego).
   * **Fortuna (Bet Builder / AKO):** $k_{\text{tax}} = 1.00$ lub bonus kursowy przy spełnieniu warunków promocji (np. min. 3 zdarzenia z kursem $\ge 1.30$ każde lub zakład Bet Builder).
   * **Superbet (AKO Boost / Super Boost):** Dynamiczny mnożnik bonusowy doliczany przy spełnieniu progu liczby zdarzeń i kursu minimalnego.
   *(Uwaga: profile promocyjne są trzymane w tabeli konfiguracyjnej z datą ważności regulaminu i możliwością przełączenia przez użytkownika na tryb „Standard 0.88×”.)*

3. **Podatek dochodowy 10% od wysokich wygranych (`> 2280.00 PLN`):**
   Jeśli wstępna wygrana $W_{\text{wstępna}} = S \cdot k_{\text{tax}} \cdot O_{\text{brutto}} > 2280.00\text{ PLN}$, pobierany jest podatek **10% od całej kwoty wygranej** (nie tylko od nadwyżki):
   $$W_{\text{netto}} = \begin{cases} W_{\text{wstępna}}, & \text{gdy } W_{\text{wstępna}} \le 2280.00 \\ 0.90 \cdot W_{\text{wstępna}}, & \text{gdy } W_{\text{wstępna}} > 2280.00 \end{cases}$$
   Generator kuponów automatycznie ostrzega użytkownika, gdy jego stawka powoduje przekroczenie progu `2280 PLN` (czasem rozbicie kuponu na dwa mniejsze kupony o połowie stawki chroni przed utratą 10% całej wygranej — kalkulator podpowie tę optymalizację matematyczną!).

---

## 3. Silnik Matematyczny i Algorytmy (Krok po Kroku)

Wszystkie obliczenia w systemie dzielą się na **4 rygorystyczne etapy potoku danych**:

### Etap 1: De-vigging (Usuwanie Marży Bukmachera)
Bukmacherzy w kursach $O_1, O_2, \dots, O_k$ ukrywają marżę (*overround*):
$$M = \sum_{i=1}^{k} \frac{1}{O_i} - 1 > 0$$
Aby wyznaczyć uczciwe prawdopodobieństwo rynkowe $p_{\text{fair}, i}$, system stosuje 3 metody (domyślnie **Shin** dla rynków 2- i 3-drogowych oraz **Power Method** jako walidator):
* **Metoda Multiplikatywna (Proporcjonalna):** $p_{\text{mult}, i} = \frac{1/O_i}{\sum_j (1/O_j)}$ (prosta, ale lekko niedoszacowuje faworytów i zawyża *longshoty* — tzw. *favorite-longshot bias*).
* **Metoda Potęgowa (Power Method):** Szukamy wykładnika $c > 0$ takiego, że $\sum_{i=1}^{k} \left(\frac{1}{O_i}\right)^c = 1$ (rozwiązywane numerycznie metodą Brenta w `scipy.optimize`).
* **Metoda Shina (Domyślna dla ostrego konsensusu):** Modeluje udział tzw. poinformowanych graczy (*insiders*) $z \in (0, 1)$, redukując błąd *favorite-longshot bias*. Rozwiązujemy równanie względem $z$:
  $$p_{\text{shin}, i}(z) = \frac{\sqrt{z^2 + 4(1-z)\frac{(1/O_i)^2}{\sum_j 1/O_j}} - z}{2(1-z)}, \quad \sum_{i=1}^{k} p_{\text{shin}, i}(z) = 1$$

---

### Etap 2: Modele Predykcyjne Specyficzne dla Każdej Kategorii Sportowej

#### A. Piłka nożna — Dwuwymiarowy Model Dixon-Coles + xG/Elo
Zwykły niezależny rozkład Poissona zaniża prawdopodobieństwo niskich remisów (`0:0`, `1:1`). Stosujemy klasyczny model **Dixon-Coles (1997)** z poprawką korelacji $\tau(x, y)$ i zanikiem czasowym $\phi(t) = \exp(-\xi \cdot \Delta t)$:
$$P(X = x, Y = y) = \tau_{\lambda, \mu, \rho}(x, y) \cdot \frac{\lambda^x e^{-\lambda}}{x!} \cdot \frac{\mu^y e^{-\mu}}{y!}$$
gdzie $\lambda = \alpha_H \cdot \beta_A \cdot \gamma_{\text{home}}$ i $\mu = \alpha_A \cdot \beta_H$ są estymowane metodą największej wiarygodności (MLE) na podstawie historycznych goli oraz **xG / xGA** (z ważeniem 70% xG / 30% rzeczywiste gole w celu redukcji losowości wykończenia).
Z macierzy wyników $(x, y) \in \{0..8\}^2$ wyliczamy bezpośrednio:
* $P(1) = \sum_{x>y} P(x,y)$, $P(X) = \sum_{x=y} P(x,y)$, $P(2) = \sum_{x<y} P(x,y)$,
* $P(\text{Over } 2.5) = \sum_{x+y \ge 3} P(x,y)$, $P(\text{BTTS Tak}) = \sum_{x\ge 1, y\ge 1} P(x,y)$,
* linie azjatyckie (np. `-0.25`, `+0.75`, `Over 2.25`) jako średnią ważoną półwygranych/zwrotów.

#### B. Koszykówka — Model Tempa (*Possession-Based*) i Rozkładu Punktów
Estymujemy oczekiwaną liczbę posiadań meczu:
$$\text{Pace}_{\text{mecz}} = \frac{\text{Pace}_A \cdot \text{Pace}_B}{\text{Pace}_{\text{liga}}}$$
oraz efektywność ataku na 100 posiadań ($\text{ORtg}, \text{DRtg}$) skorygowaną o przewagę parkietu, odpoczynek (*back-to-back penalty*) i braki kadrowe:
$$\mu_A = \frac{\text{Pace}_{\text{mecz}}}{100} \cdot \left(\text{ORtg}_A + \text{DRtg}_B - \text{AvgRtg}_{\text{liga}} + \text{HCA}\right)$$
Różnica punktów $D = S_A - S_B \sim \mathcal{N}(\mu_A - \mu_B, \sigma_{\text{diff}}^2)$ oraz suma $T = S_A + S_B \sim \mathcal{N}(\mu_A + \mu_B, \sigma_{\text{tot}}^2)$ dają analityczne prawdopodobieństwa dla każdego handicapu (*Spread*), sumy punktów (*Totals*) i *Moneyline* (z uwzględnieniem bezremisowości i małego udziału dogrywek).

#### C. Siatkówka — Hierarchiczny Model Punkt → Set → Mecz (25/25/25/25/15)
Z rankingu Elo i efektywności ataku/przyjęcia/zagrywki wyznaczamy prawdopodobieństwo wygrania pojedynczej akcji przez drużynę A: $p_{\text{pkt}}$.
Ponieważ sety 1–4 trwają do 25 punktów (z przewagą 2 pkt), a ewentualny 5. set do 15 punktów:
* Z równania rekurencyjnego łańcucha Markowa (lub rozkładu dwumianowego z rozwiązaniem gry na przewagi $P_{\text{deuce}} = \frac{p^2}{p^2 + (1-p)^2}$) wyliczamy dokładnie:
  * $P_{\text{set25}}(p_{\text{pkt}})$ — szansę wygrania seta standardowego,
  * $P_{\text{set15}}(p_{\text{pkt}})$ — szansę wygrania tie-breaka.
* Z drzewa kombinacji setowych otrzymujemy dokładne prawdopodobieństwa wyników: `3:0`, `3:1`, `3:2`, `2:3`, `1:3`, `0:3`, a stąd rynki: Zwycięzca, Handicap setowy `-1.5 / +1.5`, Over/Under 3.5 oraz 4.5 seta.

#### D. Tenis ziemny — Hierarchiczny Łańcuch Markowa O'Malleya / Barnetta-Clarke'a + Surface Elo
Tenis ma ścisłą strukturę punktową idealną do modelowania bez symulacji losowych:
1. Z nawierzchniowego **Surface Elo** (*Clay / Hard / Grass*) oraz statystyk serwisu/returnu przeciwników wyliczamy dwie wartości bazowe: $p_A$ (szansa wygrania punktu przy własnym serwisie przez A) i $p_B$ (szansa wygrania punktu przy własnym serwisie przez B).
2. Wyliczamy dokładnie prawdopodobieństwo wygrania gema serwisowego:
   $$P_{\text{gem}}(p) = p^4\left(15 - 34p + 28p^2 - 8p^3\right) + \text{(składnik deuce)} \quad \Rightarrow \quad \text{dokładne przejście stanów } (a, b)$$
3. Następnie wyliczamy prawdopodobieństwo wygrania tie-breaka (programowanie dynamiczne po stanach $(i, j)$ do 7 pkt) i całego seta $P_{\text{set}}(p_A, p_B)$, a na końcu meczu (`Best of 3` lub `Best of 5`).
4. Model generuje wiarygodne prawdopodobieństwa dla: `Zwycięzca`, `Dokładny wynik 2:0 / 2:1`, `Handicap gemowy` i `Over/Under gemów`.

#### E. Hokej na lodzie — Model Skellama (60') + Dogrywka/Karne + *Empty Net*
Dla czasu regulaminowego 60 minut modelujemy bramki obu drużyn za pomocą skorygowanego rozkładu Poissona (z wagą dla jakości bramkarza `GSAx` — *Goals Saved Above Expected* oraz siły gry w przewadze `PP%` / `PK%`). Różnica bramek $K = X - Y$ podlega **rozkładowi Skellama**:
$$P(K = k) = e^{-(\lambda+\mu)} \left(\frac{\lambda}{\mu}\right)^{k/2} I_{|k|}(2\sqrt{\lambda\mu})$$
Dla zakładów na sumę bramek (`O/U 5.5`) dodajemy stochastyczną korektę na sytuację wycofania bramkarza (*Empty Net* w ostatnich 2 minutach przy różnicy 1–2 bramek), co znacząco poprawia kalibrację rynków `Under/Over 5.5` i `-1.5`.

#### F. Tenis stołowy — Glicko-2 z Wskaźnikiem Zmienności ($\sigma$) + Markov Bo5/Bo7 (11 pkt)
Tenis stołowy (szczególnie ligi dzienne typu *TT Elite Series*, *Setka Cup*, *Liga Pro*) cechuje się błyskawiczną dynamiką, wieloma meczami jednego dnia i podwyższoną wariancją. Zwykłe Elo tu nie wystarcza — wdrażamy model dedykowany:
1. **System Glicko-2:** Oprócz rankingu siły $R$ i odchylenia $RD$, utrzymujemy parametr **zmienności (*volatility*) $\sigma_i$** każdego zawodnika oraz **zmęczenie dobowe** (liczba setów rozegranych w ciągu ostatnich 6h/24h).
2. **Łańcuch Markowa dla seta do 11 pkt (rotacja serwisu co 2 pkt, od 10:10 co 1 pkt):** Programowanie dynamiczne z rozróżnieniem przewagi na własnym serwisie vs odbiorze daje dokładne $P_{\text{set11}}(p_{\text{srv}, A}, p_{\text{rcv}, A})$ oraz oczekiwany rozkład punktów w secie.
3. **Agregacja meczu `Bo5` (do 3 wygranych setów) lub `Bo7` (WTT):** Dokładny rozkład `3:0`, `3:1`, `3:2` itd.
4. **Strażnik Wariancji (*Table Tennis Volatility Guard*):** Jeśli $\sigma_i$ przekracza próg ligowy lub próbka meczów H2H jest poniżej progu ufności, algorytm obniża wagę pewności (*shrinkage* w stronę rynku) i wyświetla na froncie wyraźną etykietę w kolorze `#F59E0B`: *„Podwyższona wariancja — ostrożna waga w kuponie”*.

---

### Etap 3: Fuzja Bayesowska z Rynkiem Ostrym i Kalibracja
Własny model statystyczny może nie znać nagłej kontuzji z rozgrzewki, dlatego nie ufamy mu ślepo w 100%. Łączymy go z bezmarżowym konsensusem ostrego rynku ($p_{\text{sharp}}$):
$$p_{\text{true}} = w_{\text{sport}} \cdot p_{\text{model}} + (1 - w_{\text{sport}}) \cdot p_{\text{sharp}}$$
*(Przykładowe wagi startowe do dostrojenia w backteście: Piłka nożna $w \approx 0.45$, Tenis $w \approx 0.40$, Tenis stołowy $w \approx 0.30$ przy wysokim $\sigma$.)*

Każdy model jest stale rozliczany historycznie przez:
* **Brier Score:** $\text{BS} = \frac{1}{N} \sum (p_i - y_i)^2$ (im bliżej 0, tym lepsza kalibracja),
* **Log-Loss:** $-\frac{1}{N} \sum [y_i \ln p_i + (1 - y_i)\ln(1 - p_i)]$ (ostro karze fałszywą pewność siebie),
* **Closing Line Value (CLV):** porównanie naszego kursu w momencie analizy z kursem zamknięcia (*closing fair line*) na minutę przed startem meczu.

---

### Etap 4: Expected Value (EV Netto PL) i Ułamkowy Kelly
Wartość oczekiwana dla legalnego polskiego bukmachera uwzględnia współczynnik podatkowy $k_{\text{tax}} \in \{0.88, 1.00\}$ (oraz potencjalny próg $k_{\text{pit}} = 0.90$):
$$\text{EV}_{\text{PL}} = p_{\text{true}} \cdot (O_{\text{book}} \cdot k_{\text{tax}} \cdot k_{\text{pit}}) - 1$$
Do rekomendacji stawki dla pojedynczego zakładu lub całego kuponu używamy **Ćwierć-Kryterium Kelly'ego ($\gamma = 0.25$)** z twardym limitem bezpieczeństwa (`max 5%` budżetu na jeden kupon):
$$b_{\text{net}} = O_{\text{book}} \cdot k_{\text{tax}} - 1, \qquad f^* = \min\left(0.05,\; 0.25 \cdot \max\left(0,\; \frac{p_{\text{true}} \cdot b_{\text{net}} - (1 - p_{\text{true}})}{b_{\text{net}}}\right)\right)$$

---

## 4. Algorytm Generatora i Personalizacji Kuponów

Użytkownik wchodzi w `/generator-kuponow` i ustawia swoje preferencje:
* **Wybrane kategorie sportowe:** np. tylko `Piłka nożna + Tenis` albo wszystkie od piłki nożnej po tenis stołowy.
* **Wybrane rynki:** np. `1X2`, `Over/Under`, `Handicapy`.
* **Profil ryzyka:**
  * *Konserwatywny:* min. $p_{\text{true}} \ge 62\%$ na nogę, maks. 2–3 zdarzenia, celowany łączny kurs `1.80–2.80`, niska zmienność $\sigma$.
  * *Zbalansowany:* min. $p_{\text{true}} \ge 50\%$ na nogę, 2–4 zdarzenia, kurs `2.50–5.50`, równowaga między `EV` a szansą trafienia.
  * *Value / Agresywny:* maks. `EV Netto` (akceptowane wyższe kursy pojedyncze `2.10–3.80`), 2–5 zdarzeń.
  * *Systemowy (np. 2z3, 3z4, 3z5):* wyliczanie prawdopodobieństwa wygrania co najmniej $k$ z $n$ kombinacji za pomocą algorytmu sumowania kombinacji Poissona-dwumianowego (*Poisson Binomial Distribution*).
* **Docelowy przedział kursu lub minimalna szansa wejścia:** np. *„Pokaż kupon o kursie min. 3.00 z maksymalną możliwą szansą matematyczną wejścia”*.
* **Tryb bukmachera i stawka:** np. `100 PLN`, tryb `Standard (0.88×)` vs `Betclic Bez Podatku (min. 2 nogi >= 1.20)`.

### Mechanizm Optymalizacji Kuponu
1. **Filtrowanie Kandydatów i Strażnik Niezależności (*Anti-Correlation Guard*):**
   * Z bazy aktywnych zdarzeń wybieramy kandydatów spełniających filtry kategorii, rynków oraz docelowych kursów użytkownika (w trybie domyślnym nie odrzucamy zdarzeń wyłącznie z powodu lekko ujemnego EV podatkowego, chyba że użytkownik włączy filtr `Tylko +EV`).
   * **Kluczowa zasada matematyczna:** Dwie selekcje z tego samego meczu (np. *Wygrana gospodarzy* + *Over 2.5*) są **silnie skorelowane**. Domyślnie generator wymusza **maksymalnie 1 zdarzenie z jednego meczu** (chyba że w trybie *Bet Builder* wyliczy łączne prawdopodobieństwo z pełnej macierzy Poissona/Dixon-Coles, zamiast naiwnie mnożyć prawdopodobieństwa!).
2. **Wyznaczenie Szansy Wejścia Kuponu:**
   Dla niezależnych zdarzeń $i = 1 \dots n$:
   $$P_{\text{kupon}} = \prod_{i=1}^{n} p_{\text{true}, i}, \qquad O_{\text{brutto}} = \prod_{i=1}^{n} O_i$$
   Jeśli zdarzenia pochodzą z tej samej ligi/turnieju w tym samym oknie czasowym lub mają lekką korelację makro, stosujemy współczynnik tłumienia korelacji lub limitujemy ekspozycję jednej ligi w kuponie.
3. **Dobór Zdarzeń (Solver / Beam Search — Maksymalizacja Szansy Wejścia):**
   * W trybie domyślnym szukamy kombinacji $S$ ($|S| \in [n_{\min}, n_{\max}]$), która **maksymalizuje matematyczną szansę wejścia $P_{\text{kupon}}(S)$** przy spełnieniu zadanego przedziału kursu $O_{\min} \le O_{\text{brutto}}(S) \le O_{\max}$ oraz reguł wybranego bukmachera (np. kurs nogi $\ge 1.20$ dla promocji bez podatku):
     $$\max_{S}\; \ln P_{\text{kupon}}(S) + \beta \cdot \text{EV}_{\text{PL}}(S) \quad (\text{gdzie w trybie „Max Szansa” } \beta \ll 1,\; \text{a w trybie „Max Value” } \beta \text{ dominuje})$$
   * **Jawność EV i Nadpisywanie Kursu PL:** Niezależnie od trybu, karta kuponu zawsze pokazuje wyliczone `EV Netto` (na czerwono z ikoną `▼`, jeśli przez marżę i podatek `0.88×` jest ujemne) oraz pozwala w 1 kliknięciu wpisać faktyczny kurs z Betclic/Fortuny/STS, przeliczając cały kupon na żywo.
4. **Wyjście (Karta Kuponu):**
   Strona zwraca przejrzysty kupon wraz z:
   * Listą nóg z podaniem kategorii, rynku, kursu pojedynczego, $p_{\text{model}}$, $p_{\text{sharp}}$ i $\text{EV}_i$,
   * **Kurs całkowity brutto**, **Współczynnik podatkowy** (`0.88×` lub `1.00×`), **Kurs realny netto**,
   * **Szansa matematyczna wejścia całego kuponu (%)**,
   * **Oczekiwana wypłata netto (PLN)** (z kontrolą progu 10% powyżej `2280 PLN`),
   * **EV całego kuponu (%)** i rekomendowana stawka wg Kelly'ego.

---

## 5. Stack Technologiczny (0 zł Produkcyjny), Baza Danych i Kontrakty API

### 5.1 Architektura Hostingu 0 zł (Gotowa pod przyszłą afiliację)
* **Frontend + Auth SSR:** **Next.js (App Router, TypeScript, Tailwind CSS)** hostowany na **Cloudflare Pages** (0 zł, dozwolony użytek komercyjny w planie darmowym).
* **Logowanie i Sesje:** **Auth.js / NextAuth v5** (Google OAuth + e-mail/Magic Link) z adapterem PostgreSQL w **Neon**.
* **Baza Danych:** **Neon PostgreSQL Free** (1 GB przestrzeni, 100 CU-h/mies., bez kasowania bazy po 30 dniach).
* **Pipeline Analityczny (2×/dzień, 0 zł):** **GitHub Actions Cron** pobiera dane darmowe (`football-data.org`, `nba_api`, NHL API, archiwa tenisa, `The Odds API` w budżecie miesięcznym), wylicza macierze prawdopodobieństw i zapisuje gotowe predykcje do Neon PostgreSQL.
* **Dynamiczne API Optymalizacji:** **FastAPI (Python 3.12)** na **Render Free** (512 MB RAM; akceptowany ~1-minutowy *cold start* po 15 min bezczynności, natomiast zwykłe przeglądanie tabel meczowych działa natychmiast bezpośrednio z Neon przez SSR Next.js).

```text
bukmacherka/
├── apps/
│   ├── web/                  # Next.js 15+ (Cloudflare Pages, Auth.js, Tailwind 60-30-10)
│   └── api/                  # FastAPI (Render Free) + skrypty cron GitHub Actions
├── packages/
│   ├── quant-engine/         # Czyste biblioteki matematyczne (NumPy, SciPy, Polars)
│   ├── bookmaker-adapters/   # Adaptery darmowych źródeł + tryb hybrydowy PL + TaxEnginePL
│   └── contracts/            # Wspólne schematy OpenAPI 3.1 + wygenerowane typy TS
├── .github/workflows/        # Cron 2×/dzień (ingestia + wyliczanie modeli do Neon)
├── design/                   # Specyfikacja 60-30-10 oraz przykłady grafik (już utworzone)
└── tests/                    # Testy jednostkowe matematyki, backtesty i testy E2E UI
```

### 5.2 Główne Tabele Bazy Danych (Neon PostgreSQL)
* `users`, `accounts`, `sessions`, `verification_tokens` — konta Auth.js (Google OAuth / e-mail) + flaga `accepted_terms_18_plus_at` i zgody RODO.
* `sports_categories` (`id`, `slug`, `name_pl`, `is_enabled_v1`, `volatility_tier`, `active_model`) — `is_enabled_v1=true` dla 4 sportów v1 (`football`, `basketball`, `tennis`, `hockey`); `false` dla Fazy 2 (`volleyball`, `table_tennis`).
* `leagues` (`id`, `sport_id`, `name`, `country`, `tier_weight`)
* `events` (`id`, `league_id`, `home_competitor_id`, `away_competitor_id`, `start_time_utc`, `status`, `surface_or_format`)
* `competitor_ratings` (`competitor_id`, `rating_elo`, `glicko_r`, `glicko_rd`, `glicko_sigma`, `xg_attack`, `xg_defense`, `updated_at`)
* `odds_snapshots`: (`time`, `event_id`, `bookmaker_key`, `market_key`, `outcome_key`, `odds_decimal`, `is_sharp_benchmark`)
* `model_predictions`: (`event_id`, `market_key`, `outcome_key`, `p_model`, `p_sharp_devigged`, `p_true`, `estimated_pl_odds`, `ev_standard_pl`, `ev_taxfree_pl`, `kelly_quarter`, `model_version`, `factual_factors_json`, `computed_at`)
* `saved_slips`: (`id`, `user_id`, `user_profile_params_json`, `custom_pl_odds_overrides_json`, `bookmaker_key`, `tax_multiplier`, `total_odds_gross`, `total_odds_net`, `joint_probability`, `slip_ev_net`, `pit_10_applies`, `created_at`)

### 5.3 Główne Endpointy API (`/api/v1`)
* `GET /categories` — lista aktywnych dyscyplin w v1 (4 sporty) z liczbą nadchodzących meczów.
* `GET /events?sport=...&market=...&min_ev=...` — lista przeanalizowanych spotkań z ostatniego zrzutu (`2×/dzień`).
* `GET /events/{id}/breakdown` — pełny rozkład Poissona/Skellama/Markowa i czynniki faktograficzne.
* `POST /slips/generate` — maksymalizuje szansę wejścia $P(\text{kupon})$ w zadanym przedziale kursu (lub opcjonalnie `+EV`), zwracając Top-3 optymalne kupony z wyliczeniem kursu brutto, netto `0.88×` i `EV`.
* `POST /slips/evaluate` — natychmiast przelicza kupon po nadpisaniu przez użytkownika kursów z Betclic/Fortuny/STS (tryb hybrydowy).
* `GET / POST / DELETE /slips/saved` — zarządzanie historią zapisanych kuponów zalogowanego użytkownika w Neon PostgreSQL.
* `GET /calibration/metrics` — aktualny Brier Score, Log-Loss i CLV wg kategorii sportowych.

---

## 6. Styl Wizualny (60-30-10) i Grafiki

Pełny przewodnik stylistyczny, uzasadnienie doboru kolorów pod kątem WCAG 2.2 oraz inwentarz wszystkich grafik znajduje się w dedykowanym pliku:
* 📄 [Specyfikacja stylu 60-30-10 i katalog grafik](file:///Users/hubertlichorobiec/Antigravity%20projects/bukmacherka/design/STYL_I_GRAFIKI.md)
* 📁 Folder z przykładami grafik: [design/examples/](file:///Users/hubertlichorobiec/Antigravity%20projects/bukmacherka/design/examples)

W skrócie przyjęto system **„Quant Slate & Emerald Terminal”**:
* **60% Dominujący:** `#0B0F19` / `#0F1624` (Obsidian Slate — tło robocze o zerowym olśnieniu).
* **30% Strukturalny:** `#131C2E` / `#1B263B` + `#0D9488` / `#047857` (karty danych, granice `#23324D`, słupki rozkładów statystycznych).
* **10% Akcenty precyzyjne:** `#10B981` (Signal Emerald dla `+EV` i prawdopodobieństwa wejścia) oraz `#F59E0B` (Alpha Amber wyłącznie na główne CTA i alerty wysokiej zmienności, np. w tenisie stołowym).

---

## 7. Szczegółowy Podział Pracy na Modele: Hydrogen vs Argon

Aby zrealizować ten projekt maksymalnie efektywnie (również w trybie równoległej pracy agentowej `/teamwork` / *Swarm*), dzielimy zadania zgodnie z profilem obu dostępnych rodzin modeli w środowisku:
* **Gemini 4 Hydrogen** (`gemini-4-hydrogen-xhigh`, `gemini-4-hydrogen-high`, `gemini-4-hydrogen-medium`) — odpowiada za **architekturę, ciężką matematykę probabilistyczną, optymalizację kombinatoryczną, integracje danych bukmacherskich, reguły podatkowe oraz weryfikację poprawności logicznej i integracji**. (Dodatkowo wyższy poziom rozumowania `xhigh` oraz krótsze okno odnawiania limitów czynią go idealnym do iteracyjnych testów numerycznych i audytu algorytmów).
* **Gemini 4 Argon** (`gemini-4-argon-high`, `gemini-4-argon-medium`, `gemini-4-argon-low`) — odpowiada za **warstwę produktową Frontend (Next.js/React/Tailwind), system komponentów UI 60-30-10, wizualizacje danych (wykresy Poissona/kalibracji), widoki kategorii sportowych, interaktywny kreator i personalizator kuponów, responsywność, dostępność WCAG oraz dokumentację i testy komponentów UI**.

Kluczowa zasada podziału: **żaden model nie edytuje tych samych plików w tym samym czasie** — granicą komunikacji jest wspólny kontrakt OpenAPI + typy TypeScript (`packages/contracts/`).

### 7.1 Macierz Własności Modułów (Ownership Matrix)

| Obszar / Moduł | Model Główny (Wariant) | Katalogi / Pliki (Wyłączna własność) | Zakres odpowiedzialności |
| :--- | :--- | :--- | :--- |
| **Koordynacja, Kontrakty API & Schemat Neon DB** | **Hydrogen** (`xhigh`) | `packages/contracts/`, `apps/api/db/` | Schemat Neon PostgreSQL (w tym tabele `users`/`saved_slips`), `openapi.yaml`, generacja typów TS dla Argona |
| **Adaptery Darmowych Danych, Cron & Silnik Podatkowy** | **Hydrogen** (`high`) | `packages/bookmaker-adapters/`, `.github/workflows/` | Budżetowy loader `The Odds API` (2×/dzień), darmowe statystyki (`football-data`, `nba_api`, NHL, CSV tenisa), `PolishTaxEngine` (12%, 0.88×, Bez Podatku, >2280 zł 10%) |
| **Rdzeń Matematyczny (De-vig, Bayes, Kelly)** | **Hydrogen** (`xhigh`) | `packages/quant-engine/core/` | Metody *Shin*, *Power*, *Multiplicative*, fuzja z `p_sharp`, `EV_PL`, ćwierć-Kelly, metryki Brier/Log-Loss/CLV |
| **Modele Sportowe (v1: 4 sporty; Faza 2: flaga)** | **Hydrogen** (`xhigh` / `high`) | `packages/quant-engine/sports/` | W v1: Dixon-Coles+xG, Koszykówka Pace/Spread, Tenis Markov+Surface Elo, Hokej Skellam; Faza 2 za flagą `ENABLE_PHASE2_SPORTS=false`: Siatkówka + Tenis stołowy Glicko-2 |
| **Generator Kuponów (Max Szansa) & FastAPI** | **Hydrogen** (`xhigh`) | `packages/quant-engine/optimizer/`, `apps/api/routes/` | Solver kombinatoryczny maksymalizujący $P(\text{kupon})$ w przedziale kursu, Anti-Correlation Guard, endpoint `evaluate` pod nadpisanie kursu PL (Render Free) |
| **Design System 60-30-10, Hero & Layout Cloudflare** | **Argon** (`high`) | `apps/web/src/styles/`, `apps/web/src/components/ui/`, `apps/web/src/app/page.tsx` | Konfiguracja Next.js pod Cloudflare Pages, tokeny 60-30-10, Hero (`hero-quant-analytics.jpg` + karty SVG), nawigacja 4 kategorii v1, stopka `18+` |
| **Auth.js (Google / E-mail), RODO & Historia Kuponów** | **Argon** (`high`) | `apps/web/src/app/auth/`, `apps/web/src/app/moje-kupony/` | Logowanie Google OAuth + e-mail z Neon PostgreSQL, panel zapisanych kuponów użytkownika, modal/polityka prywatności RODO i potwierdzenie 18+ |
| **Widoki 4 Kategorii Sportowych & Karty Meczów** | **Argon** (`high` / `medium`) | `apps/web/src/app/analiza/`, `apps/web/src/app/mecz/` | Strony 4 aktywnych kategorii v1 (Piłka nożna, Koszykówka, Tenis, Hokej) czytane bezpośrednio z Neon SSR, tabele kursów i badge marży |
| **Wykresy i Wizualizacje Danych (Data-Viz)** | **Argon** (`high`) | `apps/web/src/components/charts/` | Heatmapa Poissona 0:0–4:4, wykres rozkładu punktów, krzywa kalibracji *Reliability Diagram*, wykres ruchu kursów CLV |
| **Generator Kuponów + Edycja Kursu PL w 1 kliknięciu** | **Argon** (`high`) | `apps/web/src/app/generator-kuponow/`, `apps/web/src/components/slip/` | Panel personalizacji (kategorie, cel kursu, stawka, tryb podatkowy), **inline edycja kursu z STS/Fortuny/Betclic**, ostrzeżenie przy ujemnym EV |
| **Testy Matematyczne & Backtesty** | **Hydrogen** (`medium` / `high`) | `tests/quant/`, `tests/api/` | Testy jednostkowe prawdopodobieństw ($\sum P = 1$), tolerancja numeryczna Shina, walidacja reguł podatkowych PL, testy limitu zapytań API |
| **Testy UI, Auth, WCAG & Cloudflare E2E** | **Argon** (`medium` / `low`) | `tests/e2e/`, `apps/web/src/mocks/` | Testy Playwright/Vitest (logowanie, nadpisywanie kursu PL, próg 2280 PLN, *Never Color Alone*, responsywność mobile/desktop) |

---

### 7.2 Harmonogram Fazowy (Pipeline Wykonawczy)

#### Faza 0: Kontrakt, Auth & Fundamenty (Równoległy start)
* **Hydrogen (`xhigh`):** Tworzy strukturę monorepo, schemat **Neon PostgreSQL** (tabele danych sportowych + tabele `users`/`saved_slips`), `packages/contracts/openapi.yaml` oraz generuje paczkę typów TypeScript i deterministyczne mocki JSON.
* **Argon (`high`):** Konfiguruje `Next.js` pod **Cloudflare Pages**, wgrywa tokeny 60-30-10 i zasoby z `design/examples/`, konfiguruje **Auth.js** (Google OAuth + e-mail), stronę Hero (`hero-quant-analytics.jpg` + karty SVG) oraz nawigację 4 kategorii v1 + stopkę RODO / `18+`.
* **Bramka odbioru Fazy 0:** `openapi.yaml` przechodzi walidację, logowanie działa lokalnie z bazą Neon, a szkielet strony renderuje się w palecie 60-30-10.

#### Faza 1: Cron 0 zł + Rdzeń Matematyczny (Hydrogen) ∥ Tabele 4 Kategorii i Moje Kupony (Argon)
* **Hydrogen (`xhigh`):** Implementuje moduł `de-vig` (*Shin*, *Power*, *Multiplicative*), silnik podatkowy `PolishTaxEngine` (`0.88×`, promocje bez podatku, próg `2280 zł`), kalkulator `EV_PL` i ułamkowy Kelly.
* **Hydrogen (`high`):** Implementuje pipeline **GitHub Actions (2×/dzień)** z budżetowaniem limitów darmowych (`The Odds API` + darmowe statystyki lig v1), zapisujący gotowe snapshoty do Neon PostgreSQL.
* **Argon (`high`):** Buduje bazowe komponenty (`OddsBadge`, `EvPill` z ikoną `▲`/`▼`, `TaxFactorBadge`, `CategorySelector`) oraz widoki 4 aktywnych kategorii v1 (`/analiza/[sport]`) i widok `/moje-kupony`.
* **Argon (`medium`):** Implementuje stronę `/metodologia`, `/backtest-i-kalibracja` oraz podstronę polityki prywatności RODO i zasad 18+.

#### Faza 2: 4 Silniki Sportowe + Generator Max-Szansa (Hydrogen) ∥ Wykresy i Hybrydowy Kalkulator (Argon)
* **Hydrogen (`xhigh`):** Implementuje 4 silniki predykcyjne v1 (*Dixon-Coles* dla Piłki nożnej, *Pace/Spread* dla Koszykówki, *Markov+Surface Elo* dla Tenisa, *Skellam+Empty Net* dla Hokeja) oraz moduły Fazy 2 (*Siatkówka*, *Tenis stołowy Glicko-2*) ukryte za flagą.
* **Hydrogen (`xhigh`):** Implementuje `SlipOptimizer` maksymalizujący $P(\text{kupon})$ w zadanym przedziale kursu (z opcją `+EV`), endpoint `POST /slips/evaluate` i wdraża lekkie FastAPI na **Render Free**.
* **Argon (`high`):** Buduje komponenty Data-Viz (`PoissonMatrixHeatmap`, `CalibrationCurveChart`, `OddsMovementChart`, `ProbabilityGaugeRing`) oraz `/generator-kuponow` z **edycją kursu bukmachera PL w 1 kliknięciu**, jawnym alertem ujemnego EV i zapisem kuponu na konto zalogowanego użytkownika.

#### Faza 3: Integracja E2E, Kalibracja i Weryfikacja Cross-Model
* **Hydrogen (`high`) + Argon (`high`):** Podpięcie produkcyjnego wdrożenia **Cloudflare Pages** pod **Neon PostgreSQL** i **Render Free FastAPI**, weryfikacja obsługi ~1 min *cold-startu* API w UI (czytelny stan ładowania przy generowaniu dynamicznym, podczas gdy listy meczów ładują się natychmiast z Neon).
* **Weryfikacja Krzyżowa (Kluczowy mechanizm jakości):**
  * **Hydrogen (`xhigh`)** audytuje warstwę UI Argona pod kątem poprawności matematycznej przeliczeń przy ręcznym nadpisywaniu kursu PL, obsługi progu `2280 PLN` oraz spójności z kontraktem API.
  * **Argon (`high`)** uruchamia testy E2E Playwright (logowanie Google/e-mail, zapis kuponu, 4 kategorie sportowe, zmiana kursu PL, testy WCAG i proporcji 60-30-10).
* **Hydrogen (`medium`):** Uruchamia pełny zestaw testów numerycznych (`pytest`) sprawdzających niezmienniki probabilistyczne i limity zużycia darmowych zapytań API.

---

### 7.3 Rekomendacja Uruchomienia w Trybie Swarm (`/teamwork`)
Gdy zdecydujesz się przejść do implementacji tego planu, można go uruchomić jako skoordynowany zespół agentów w jednym przebiegu:
* **Koordynator:** `gemini-4-hydrogen-xhigh`
* **Worker `quant-math`:** `gemini-4-hydrogen-xhigh` (4 silniki sportowe v1, de-vig, optymalizator Max-Szansa)
* **Worker `feed-tax-api`:** `gemini-4-hydrogen-high` (cron GitHub Actions 2×/dzień, Neon PostgreSQL, FastAPI na Render, PolishTaxEngine)
* **Worker `ui-auth`:** `gemini-4-argon-high` (Next.js na Cloudflare Pages, Auth.js Google/e-mail, Hero, RODO, generator kuponów z edycją kursu PL)
* **Worker `dataviz-qa`:** `gemini-4-argon-medium` (wykresy, SVG, testy E2E UI)

---

## 8. Zgodność Prawna w Polsce (Compliance 18+ i RODO)

Projekt ma charakter **wyłącznie edukacyjno-analityczny i informacyjny** — nie przyjmuje zakładów ani nie pośredniczy w płatnościach:
1. Prezentowane kursy oraz przeliczniki podatkowe dotyczą wyłącznie legalnych operatorów posiadających aktualne zezwolenie Ministra Finansów RP (np. Betclic, Superbet, Fortuna, STS, LV BET).
2. Rejestracja konta wymaga akceptacji regulaminu potwierdzającego **pełnoletność (18+)** oraz spełnienia obowiązku informacyjnego **RODO** (prawo wglądu i usunięcia zapisanych kuponów oraz konta w Neon PostgreSQL).
3. W stopce oraz na karcie każdego wygenerowanego kuponu znajduje się wyraźna informacja:
   * *„Serwis przeznaczony wyłącznie dla osób pełnoletnich (18+). Analizy mają charakter statystyczno-matematyczny i nie stanowią gwarancji wygranej. Hazard wiąże się z ryzykiem uzależnienia.”*
4. Interfejs nie używa manipulacyjnych sformułowań („pewniak”, „100% wejdzie”, „łatwy zysk”), zastępując je precyzyjnym językiem rachunku prawdopodobieństwa (`Szansa wejścia P = 26.0%`, `EV Netto = -4.2% (wpływ podatku 12%)`, `Odchylenie standardowe`).
