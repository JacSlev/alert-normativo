# Fonti da monitorare

54 fonti ufficiali organizzate per ambito. File sorgente: `assets/Link_Monitoraggio.xlsx`.

## Cross Finance (8 fonti)

| Fonte | URL | Accesso preferito |
|---|---|---|
| CONSOB | https://www.consob.it/web/area-pubblica/home | HTML |
| Gazzetta Ufficiale | https://www.gazzettaufficiale.it/ | HTML |
| EUR-Lex | https://eur-lex.europa.eu/homepage.html?locale=it | HTML |
| ICMA | https://www.icmagroup.org/ | HTML |
| FSB | https://www.fsb.org/ | HTML |
| EDPB | https://www.edpb.europa.eu/edpb_it | HTML |
| IOSCO | https://www.iosco.org/ | HTML |
| Commissione Europea | https://commission.europa.eu/index_it | HTML |

## Cross Finance — Sostenibilità (6 fonti)

| Fonte | URL | Accesso preferito |
|---|---|---|
| ESMA Sustainable Finance | https://www.esma.europa.eu/esmas-activities/sustainable-finance | HTML |
| EFRAG | https://www.efrag.org/en/news-and-calendar/news | HTML |
| Commissione UE news | https://commission.europa.eu/news-and-media/news_en | HTML |
| Eurosif | https://www.eurosif.org/ | HTML |
| ANIA pubblicazioni | https://www.ania.it/pubblicazioni | HTML |
| Dirittobancario.it — Finanza e mercati | https://www.dirittobancario.it/sez/finanza-e-mercati/ | HTML |

## Banking (13 fonti)

| Fonte | URL | Accesso preferito |
|---|---|---|
| EBA press releases | https://www.eba.europa.eu/publications-and-media/press-releases | RSS |
| Banca d'Italia | https://www.bancaditalia.it/ | HTML |
| Banca d'Italia — Archivio norme | https://www.bancaditalia.it/compiti/vigilanza/normativa/archivio-norme/ | HTML |
| Banca d'Italia — Consultazioni | https://www.bancaditalia.it/compiti/vigilanza/normativa/consultazioni/index.html | HTML |
| Banca d'Italia — Approfondimenti | https://www.bancaditalia.it/media/approfondimenti/index.html | HTML |
| Banca d'Italia — Comunicati BCE | https://www.bancaditalia.it/media/bce-comunicati/index.html | HTML |
| BCE | https://www.ecb.europa.eu/press/pr/date/html/index.it.html | RSS |
| BIS/BCBS | https://www.bis.org/bcbs/publications.htm?m=3%7C14%7C566 | HTML |
| ABI news | https://www.abi.it/info/abi-news/ | HTML |
| ABI comunicati stampa | https://www.abi.it/info/comunicati-stampa/ | HTML |
| ABI eventi | https://www.abi.it/prossimi-eventi/ | HTML |
| Dirittobancario.it — Flash news banca | https://www.dirittobancario.it/cat/flash-news/?sez=banca | HTML |
| Dirittobancario.it — Approfondimenti banche | https://www.dirittobancario.it/cat/approfondimenti/banche-e-intermediari/ | HTML |

## Insurance (27 fonti)

| Fonte | URL | Accesso preferito |
|---|---|---|
| IVASS — Regolamenti | https://www.ivass.it/normativa/nazionale/secondaria-ivass/regolamenti/index.html | HTML |
| IVASS — Provvedimenti | https://www.ivass.it/normativa/nazionale/secondaria-ivass/normativi-provv/index.html | HTML |
| IVASS — Comunicazioni | https://www.ivass.it/normativa/nazionale/secondaria-ivass/comunicazioni/index.html | HTML |
| IVASS — Lettere | https://www.ivass.it/normativa/nazionale/secondaria-ivass/lettere/index.html | HTML |
| IVASS — Consultazioni | https://www.ivass.it/normativa/nazionale/secondaria-ivass/pubb-cons/index.html | HTML |
| IVASS — Esiti consultazioni | https://www.ivass.it/normativa/nazionale/secondaria-ivass/esiti-pubb-cons/index.html | HTML |
| IVASS — Media | https://www.ivass.it/media/index.html | HTML |
| EIOPA news | https://www.eiopa.europa.eu/media/news_en | RSS |
| EIOPA eventi | https://www.eiopa.europa.eu/media/events_en?prefLang=it | HTML |
| EIOPA homepage | https://www.eiopa.europa.eu/ | HTML |
| EIOPA document library | https://www.eiopa.europa.eu/document-library_en | HTML |
| EIOPA tools and data | https://www.eiopa.europa.eu/tools-and-data_en | HTML |
| EIOPA speeches | https://www.eiopa.europa.eu/media/speeches-presentations_en | HTML |
| EIOPA interviews | https://www.eiopa.europa.eu/media/interviews-contributions_en | HTML |
| ANIA pubblicazioni | https://www.ania.it/pubblicazioni | HTML |
| ANIA comunicati | https://www.ania.it/comunicati | HTML |
| ANIA — categoria 111377 | https://www.ania.it/pubblicazioni/-/categories/111377 | HTML |
| ANIA — categoria 53704 | https://www.ania.it/pubblicazioni/-/categories/53704 | HTML |
| ANIA — categoria 53705 | https://www.ania.it/pubblicazioni/-/categories/53705 | HTML |
| ANIA — categoria 53703 | https://www.ania.it/pubblicazioni/-/categories/53703 | HTML |
| ANIA — categoria 52472 | https://www.ania.it/pubblicazioni/-/categories/52472 | HTML |
| Insurance Europe — news | https://www.insuranceeurope.eu/news | HTML |
| Insurance Europe — publications | https://www.insuranceeurope.eu/publications | HTML |
| Insurance Europe — events | https://www.insuranceeurope.eu/events | HTML |
| IAIS news | https://www.iaisweb.org/page/news | HTML |
| IAIS consultations | https://www.iaisweb.org/page/consultations | HTML |
| IAIS events | https://www.iaisweb.org/page/events | HTML |

## Parametri di scraping

- Finestra temporale: ultimi `FINESTRA_GIORNI` giorni (default 7)
- Deduplicazione: confronto su URL — non processare notizie già presenti nel file Excel
- Retry: max 3 tentativi con backoff esponenziale (1s, 2s, 4s)
- Timeout per richiesta: 10 secondi
- Se una fonte è irraggiungibile: loggare l'errore e continuare con le altre
