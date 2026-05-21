# Fonti da monitorare

Fonti ufficiali organizzate per ambito. La configurazione è in `config.py` (`RSS_SOURCES`, `HTML_SOURCES`, `FONTE_AMBITO`).

Legenda accesso: **RSS** = feedparser, **HTML** = requests + BeautifulSoup4, **Selenium** = Chrome headless (JS-rendered).

---

## Banking

| Fonte | URL principale | Accesso |
|---|---|---|
| EBA | https://www.eba.europa.eu/rss.xml | RSS |
| BCE | https://www.ecb.europa.eu/rss/press.html | RSS |
| ABI (news, comunicati, eventi) | https://www.abi.it/feed | RSS (3 feed) |
| Dirittobancario — Flash news banca | https://www.dirittobancario.it/cat/flash-news/feed/ | RSS |
| Dirittobancario — Approfondimenti banche | https://www.dirittobancario.it/cat/approfondimenti/banche-e-intermediari/feed/ | RSS |
| Banca d'Italia — Homepage | https://www.bancaditalia.it/ | Selenium |
| Banca d'Italia — Archivio norme | https://www.bancaditalia.it/compiti/vigilanza/normativa/archivio-norme/ | Selenium |
| Banca d'Italia — Consultazioni | https://www.bancaditalia.it/compiti/vigilanza/normativa/consultazioni/ | Selenium |
| Banca d'Italia — Approfondimenti | https://www.bancaditalia.it/media/approfondimenti/ | Selenium (`#bdi_form_results li`) |
| Banca d'Italia — Ricerche/Infokit | https://www.bancaditalia.it/media/infokit/ | Selenium (`#bdi_form_results li`) |
| Banca d'Italia — Comunicati BCE | https://www.bancaditalia.it/media/bce-comunicati/ | Selenium |
| BIS/BCBS | https://www.bis.org/bcbs/publications.htm | Selenium |
| BCE — Pubblicazioni tecniche | https://www.ecb.europa.eu/pub/pubbydate/html/index.en.html | Selenium |
| AMLA — News | https://www.amla.europa.eu/news-media/news-articles_en (RSS: /node/19/rss_en) | HTML (RSS interno) |
| AMLA — Document library | https://www.amla.europa.eu/resources/document-library_en (RSS: /node/105/rss_en) | HTML (RSS interno) |

---

## Insurance

| Fonte | URL principale | Accesso |
|---|---|---|
| EIOPA (news) | https://www.eiopa.europa.eu/node/4816/rss_en | RSS |
| EIOPA — Events | https://www.eiopa.europa.eu/media/events_en | HTML |
| EIOPA — Document library | https://www.eiopa.europa.eu/document-library_en | HTML |
| EIOPA — Speeches | https://www.eiopa.europa.eu/media/speeches-presentations_en | HTML |
| EIOPA — Interviews | https://www.eiopa.europa.eu/media/interviews-contributions_en | HTML |
| IVASS — Regolamenti | https://www.ivass.it/normativa/nazionale/secondaria-ivass/regolamenti/index.html | HTML |
| IVASS — Provvedimenti | https://www.ivass.it/normativa/nazionale/secondaria-ivass/normativi-provv/index.html | HTML |
| IVASS — Comunicazioni | https://www.ivass.it/normativa/nazionale/secondaria-ivass/comunicazioni/index.html | HTML |
| IVASS — Lettere | https://www.ivass.it/normativa/nazionale/secondaria-ivass/lettere/index.html | HTML |
| IVASS — Consultazioni | https://www.ivass.it/normativa/nazionale/secondaria-ivass/pubbliche-consultazioni/index.html | HTML |
| IVASS — Esiti consultazioni | https://www.ivass.it/normativa/nazionale/secondaria-ivass/esiti-pubb-cons/index.html | HTML |
| IVASS — Media/Comunicati | https://www.ivass.it/media/comunicati/index.html | HTML |
| ANIA — Comunicati | https://www.ania.it/comunicati | Selenium |
| ANIA — Pubblicazioni | https://www.ania.it/pubblicazioni | Selenium |
| ANIA — Categoria 111377 | https://www.ania.it/pubblicazioni/-/categories/111377 | Selenium |
| ANIA — Categoria 53704 | https://www.ania.it/pubblicazioni/-/categories/53704 | Selenium |
| ANIA — Categoria 53705 | https://www.ania.it/pubblicazioni/-/categories/53705 | Selenium |
| ANIA — Categoria 53703 | https://www.ania.it/pubblicazioni/-/categories/53703 | Selenium |
| ANIA — Categoria 52472 | https://www.ania.it/pubblicazioni/-/categories/52472 | Selenium |
| Insurance Europe — News | https://www.insuranceeurope.eu/news | HTML |
| Insurance Europe — Publications | https://www.insuranceeurope.eu/publications | HTML |
| Insurance Europe — Events | https://www.insuranceeurope.eu/events | HTML |
| IAIS — News | https://www.iais.org/news-and-events/latest-news/ | HTML |
| IAIS — Consultations | https://www.iais.org/consultations/ | HTML |
| IAIS — Events | https://www.iais.org/news-and-events/stakeholder-events/ | HTML |

---

## Cross Finance

| Fonte | URL principale | Accesso |
|---|---|---|
| FSB | https://www.fsb.org/feed | RSS |
| EDPB | https://www.edpb.europa.eu/feed/news_it | RSS |
| ESMA | https://www.esma.europa.eu/rss.xml | RSS |
| Eurosif | https://www.eurosif.org/feed/ | RSS |
| Dirittobancario — Finanza e mercati | https://www.dirittobancario.it/sez/finanza-e-mercati/feed/ | RSS |
| CONSOB | https://www.consob.it/web/area-pubblica/home | HTML |
| Gazzetta Ufficiale | https://www.gazzettaufficiale.it/home | Selenium |
| EUR-Lex | https://eur-lex.europa.eu/homepage.html?locale=it | Selenium (best-effort) |
| ICMA | https://www.icmagroup.org/ | HTML |
| IOSCO | https://www.iosco.org/ | HTML (best-effort) |
| Commissione Europea — Homepage | https://commission.europa.eu/index_it | HTML |
| Commissione Europea — News | https://commission.europa.eu/news-and-media/news_en | HTML |
| EFRAG | https://www.efrag.org/en/news-and-calendar/news | HTML |

---

## Note operative

- **Finestra temporale:** ultimi `FINESTRA_GIORNI` giorni (default 7, configurabile in `.env`)
- **Deduplicazione:** confronto su URL — le notizie già presenti nell'Excel non vengono reinserite
- **Timeout richieste:** 15 secondi per HTTP statico, 20 secondi per Selenium
- **Errori per fonte:** se una fonte è irraggiungibile, lo script logga l'errore e continua con le altre
- **Best-effort:** EUR-Lex, IOSCO e AMLA possono restituire 0 notizie se il sito è irraggiungibile o blocca l'accesso
- **BCE Publications:** la pagina `pub/pubbydate` è JS-rendered; usa Selenium. Il feed RSS BCE esistente copre solo press release e discorsi — non i documenti tecnici/working papers
- **AMLA:** le funzioni usano internamente i feed RSS ufficiali AMLA; in caso di errore loggano `[WARNING]` e restituiscono lista vuota
- **IAIS:** dominio migrato da `iaisweb.org` a `iais.org` (aggiornato nel codice)
- **IVASS Consultazioni:** URL aggiornata da `/pubb-cons/index.html` a `/pubbliche-consultazioni/index.html`
- **IVASS Media:** URL aggiornata da `/media/index.html` a `/media/comunicati/index.html`
