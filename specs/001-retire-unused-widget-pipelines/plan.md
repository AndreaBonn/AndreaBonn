# Retire unused widget pipelines

## Obiettivo

Spegnere le pipeline che generano `snake_basket.gif`, `tamagotchi.svg` e `last_commit.svg`, asset
non più referenziati dal README, mantenendo l'aggiornamento quotidiano di `assets/visitors.json`.

## Definition of Done

- Il workflow `update_profile.yml` è YAML valido e la lista degli step è esattamente: Checkout,
  Setup uv, Install dependencies, Run tests, Quote of the day, Today in NBA history, Total stars,
  Total forks, Per-repo star badges, Update visitors counter, Commit updated assets.
- Ogni path elencato nella riga `git add` esiste ed è tracciato (`git ls-files --error-unmatch`).
- `uv run python scripts/update_visitors.py` aggiorna `assets/visitors.json` mantenendo le chiavi
  `last_komarev`, `total`, `history`, e logga le due cifre.
- Lo step visitors non dichiara `SNAKE_TOKEN`: komarev è un endpoint pubblico senza auth
  (`scripts/common/visitors.py:66`).
- Nessuna occorrenza di `snake_basket|tamagotchi|scoreboard|last_commit|force_snake` in
  `.github/`, `scripts/`, `tests/`, `README.md`, `pyproject.toml`.
  Esclusi `docs/CODE_ROAST_REPORT.md` e `docs/REPORT_ATTIVITA.md`: sono report storici che citano
  quel codice come cronaca di sessioni passate, riscriverli falsificherebbe un archivio.
- Floor verde: `ruff check`, `ruff format --check`, `pytest --cov` con coverage >= 85, `bandit`.

## Assunzioni

- `assets/visitors.json` continua a produrre un commit giornaliero pur senza widget che lo
  renderizzi: è il senso esplicito della richiesta di tenere viva la catena.
- La history git non va riscritta: si cancellano i file, i blob restano nei commit passati e la
  dimensione del clone non cala. Atteso.
- Il secret `SNAKE_TOKEN` resta configurato: serve a `total_stars`, `total_forks`, `repo_stars`,
  `tech_stack`. Va rimosso solo dallo step tamagotchi che sparisce.
- `update_tech_stack.yml` è fuori scope, non referenzia asset rimossi.

## Approccio

Commit unico. Rimozione di script/test/asset e potatura del workflow sono lo stesso cambiamento
logico: un commit parziale lascerebbe il workflow con un `git add` su path inesistenti, cioè il job
giornaliero rotto in produzione. L'atomicità qui vale più della separazione per tipo di file.

Per la catena visitors serve un nuovo entry point, perché `fetch_visitor_count()` aveva come unico
chiamante `tamagotchi.py:257`. `scripts/update_visitors.py` è quel chiamante: 7 righe, nessuna
logica propria, delega tutto a `common/visitors.py`.

## Rischi

| Rischio | Impatto | Mitigazione |
|---|---|---|
| `git add` su path cancellati | Il job fallisce con `fatal: pathspec` e smette di committare **tutti** gli asset, non solo quelli rimossi | Verify automatico con `git ls-files --error-unmatch` su ogni path |
| Catena visitors spenta in silenzio | `visitors.json` smette di aggiornarsi senza errore visibile, perché nessun widget lo renderizza | Controllo del primo run schedulato dopo il merge |
| `SNAKE_TOKEN` rimosso per eccesso di zelo dagli step stars/forks/badges | 401 sulla GitHub API | Non toccare quei tre step |
| Workflow YAML rotto | Il job fallisce alle 7:00 UTC in silenzio | Parse YAML esplicito prima del commit |

## Criteri di successo

Workflow parsabile con 11 step attesi; `git add` con soli path tracciati; script visitors eseguito
davvero a runtime, non solo importato; floor verde; grep pulito nelle aree in scope.
Conferma finale in produzione: il primo run schedulato chiude verde e il commit automatico include
`assets/visitors.json`.
