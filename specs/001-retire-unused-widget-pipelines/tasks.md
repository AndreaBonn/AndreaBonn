# Tasks — Retire unused widget pipelines

| id | dipendenze | requisito tracciato | descrizione | verify |
|---|---|---|---|---|
| T1 | - | DoD: entry point visitors | Creare `scripts/update_visitors.py` + `tests/test_update_visitors.py` | `uv run pytest tests/test_update_visitors.py` verde dopo aver visto il rosso |
| T2 | T1 | DoD: grep pulito | `git rm` di 4 script, 3 test, 3 asset delle pipeline dismesse | `git status --short` mostra le 10 D |
| T3 | - | DoD: lista step | Rimuovere input `force_snake`, step `Get day of week`, step `Snake Basket` | `grep -nE "day of week\|Snake Basket\|steps.day\|force_snake"` senza match |
| T4 | T1, T3 | DoD: lista step + step senza env | Sostituire step `Tamagotchi and last commit` con `Update visitors counter` | Parse YAML: lo step esiste e non ha chiave `env` |
| T5 | T2, T4 | DoD: path tracciati | Potare la riga `git add` dai tre asset rimossi | `git ls-files --error-unmatch` su ogni path esce 0 |
| T6 | T5 | DoD: runtime | Eseguire davvero `update_visitors.py` e osservare `visitors.json` | Riga INFO attesa + JSON valido con le 3 chiavi |
| T7 | T6 | DoD: floor verde | ruff check, ruff format --check, pytest --cov, bandit | Tutti exit 0, coverage >= 85 |
| T8 | T7 | - | Gate `code-reviewer` sul diff, poi commit unico | Report senza finding bloccanti |

Stato finale: T1-T8 completati nel commit `88e5e26`.

Fuori piano, emerso dal gate `/analyze`: `pip-audit` falliva su `pip 26.1.2` (PYSEC-2026-3721),
con la CI di `main` già rossa da prima di questo lavoro. Risolto a parte nel commit `5d709f6`.
La DoD del piano elencava un floor incompleto rispetto a `ci.yml`, che include anche `pip-audit`.
