# Skill-Creator

Una repo per creare skill per agenti AI. Tu dai due informazioni, la piattaforma e il compito ripetitivo, e ottieni una repo git completa con dentro la skill, pronta da installare.

Ogni skill segue lo [standard aperto Agent Skills](https://agentskills.io) e le regole ufficiali di Anthropic, OpenAI, Google Antigravity e OpenCode. Per questo funziona senza modifiche su agenti diversi.

## Come si usa

Apri questa cartella con il tuo agente (Claude Code, Codex, OpenCode, Antigravity) e scrivi la richiesta. Per esempio:

> Piattaforma: Claude Code. Compito: ogni lunedì trasformo l'export CSV delle vendite in un report con i totali per categoria.

L'agente segue le istruzioni di `skills/skill-repo-creator/SKILL.md`:

1. Controlla la documentazione ufficiale della piattaforma.
2. Progetta la skill e scrive tre casi di test.
3. Crea la repo della skill nella cartella accanto a questa: `../<nome-skill>/`.
4. Scrive i contenuti ed esegue il validatore finché non restano errori.
5. Prova la skill, fa il commit locale e ti consegna il resoconto in cinque parti: analisi tecnica, skill completa, installazione, test pratici, fonti ufficiali.

L'agente non fa push, non crea repo remote e non installa nulla nei tuoi agenti, a meno che tu non lo chieda.

Se hai creato la cartella `.claude/skills` a sessione già aperta, in Claude Code esegui `/reload-skills` per far comparire la skill.

## Che cosa contiene ogni repo generata

```text
<nome-skill>/
├── skills/<nome-skill>/
│   ├── SKILL.md              la skill: istruzioni e metadati
│   └── evals/                casi di test e richieste di attivazione
├── scripts/validate_skill.py validatore, da eseguire prima di ogni commit
├── README.md                 a cosa serve, come si installa, prompt di prova, fonti
├── AGENTS.md                 regole per restare indipendenti dall'agente
├── CLAUDE.md                 importa AGENTS.md per Claude Code
├── CHANGELOG.md
├── LICENSE                   MIT
├── .gitignore
├── .claude/skills/<nome-skill>   link alla skill, per provarla subito
└── .agents/skills/<nome-skill>   link alla skill, per provarla subito
```

L'agente installa solo la cartella `skills/<nome-skill>/`. Tutto il resto è documentazione e strumenti.

## Le regole che ogni skill rispetta

- **Frontmatter portabile.** Solo i sei campi dello standard: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.
- **Nome.** Lettere minuscole, numeri e trattini, al massimo 64 caratteri, uguale al nome della cartella, senza le parole `anthropic` e `claude`.
- **Descrizione.** In terza persona, dice che cosa fa la skill e quando usarla, al massimo 1024 caratteri.
- **Corpo.** Meno di 500 righe, senza sintassi, strumenti o percorsi legati a un solo agente.
- **Struttura fissa.** Obiettivo, dati in ingresso, regole, procedura, formato di uscita, controlli di qualità, eccezioni, esempi.
- **Test.** Almeno tre casi di test e una serie di richieste che devono, o non devono, attivare la skill.
- **Licenza MIT.**

Il validatore controlla queste regole e blocca la consegna finché ci sono errori. Il dettaglio è in `skills/skill-repo-creator/references/`:

| File | Contenuto |
|---|---|
| `authoring-rules.md` | Come scrivere nome, descrizione, corpo, script e test, con la fonte di ogni regola |
| `portability.md` | Le regole per restare indipendenti dall'agente |
| `platforms.md` | Dove ogni piattaforma installa le skill e quali limiti ha, con la data di verifica |

## Struttura di questa repo

```text
Skill-Creator/
├── skills/skill-repo-creator/
│   ├── SKILL.md                  la procedura che l'agente segue
│   ├── references/               regole di scrittura, portabilità, piattaforme
│   ├── scripts/                  scaffold_skill_repo.py e validate_skill.py
│   ├── assets/repo-template/     i modelli dei file di ogni repo generata
│   └── evals/                    casi di test di questa skill
├── tests/                        test automatici dei due script
├── fonti/                        l'elenco delle fonti ufficiali
├── AGENTS.md                     istruzioni per l'agente che lavora qui
└── CLAUDE.md                     importa AGENTS.md per Claude Code
```

## Comandi utili

```bash
# Controllare questa repo
python3 skills/skill-repo-creator/scripts/validate_skill.py .

# Eseguire i test degli script
python3 -B -m unittest discover -s tests

# Creare a mano lo scheletro di una nuova repo
python3 skills/skill-repo-creator/scripts/scaffold_skill_repo.py \
  --name nome-skill --description "Che cosa fa. Use when ..." --dest .. --lang it

# Controllare una repo generata
python3 ../nome-skill/scripts/validate_skill.py
```

## Usare la skill fuori da questa cartella

Per creare skill da qualsiasi progetto, copia la cartella della skill tra quelle del tuo agente. Per Claude Code:

```bash
cp -R skills/skill-repo-creator ~/.claude/skills/
```

I percorsi degli altri agenti sono in `skills/skill-repo-creator/references/platforms.md`.

## Fonti

L'elenco di partenza è in `fonti/links-best-practices.md`. Stato della verifica al 18 novembre 2026:

| Fonte | Stato |
|---|---|
| [OpenCode: skills](https://opencode.ai/docs/skills/) | Letta |
| [Google Antigravity: skills](https://antigravity.google/docs/skills/) | Letta |
| [Anthropic: best practice per le skill](https://platform.claude.com/docs/it/agents-and-tools/agent-skills/best-practices) | Letta |
| [OpenAI Academy: skills](https://openai.com/academy/skills/) | Non letta: la pagina risponde con errore 403 alle richieste automatiche |

Per OpenAI le regole vengono dalla documentazione ufficiale [Build skills](https://learn.chatgpt.com/docs/build-skills). Le altre fonti lette sono la [specifica Agent Skills](https://agentskills.io/specification), le sue guide su [valutazione](https://agentskills.io/skill-creation/evaluating-skills) e [descrizioni](https://agentskills.io/skill-creation/optimizing-descriptions), e la documentazione di [Claude Code](https://code.claude.com/docs/en/skills).

Per aggiungere la pagina di OpenAI Academy, salvala dal browser nella cartella `fonti/` e chiedi all'agente di aggiornare le regole.

## Licenza

[MIT](LICENSE) © 2026 Max Brandini
# Skill-Creator
