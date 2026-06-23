# Come incorporare il video di presentazione nel README

File pronti in `assets/`:
- `intro.mp4` — il video (1080p, 42s, con voce Giuseppe + musica)
- `intro-poster.jpg` — frame di anteprima (thumbnail)

## Opzione A (consigliata) — player inline con audio

GitHub mostra un player HTML5 nativo (con audio e controlli) solo per i video
caricati tramite la sua interfaccia. Una volta sola:

1. Vai su github.com sul tuo profilo, modifica il README.
2. Trascina `intro.mp4` dentro l'editor: GitHub lo carica e genera un link tipo
   `https://github.com/user-attachments/assets/xxxxxxxx`.
3. Incolla quel link dove vuoi il video (in cima al README). Si trasforma da solo
   nel player.

## Opzione B — anteprima cliccabile (funziona subito dal file nel repo)

Se preferisci tenere il file versionato nel repo, incolla questo in cima al README.
Mostra il poster; al click apre il video con audio.

```html
<p align="center">
  <a href="https://github.com/AndreaBonn/AndreaBonn/raw/main/assets/intro.mp4">
    <img src="./assets/intro-poster.jpg" alt="Andrea Bonacci - terminal intro" width="720">
  </a>
</p>
<p align="center"><i>Terminal intro - click per riprodurre (con audio)</i></p>
```

Nota: il tag `<video src="./assets/intro.mp4">` con percorso relativo NON viene
renderizzato da GitHub (sanitizzazione). Per il player inline serve l'Opzione A.
