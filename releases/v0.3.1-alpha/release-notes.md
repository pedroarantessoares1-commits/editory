# App Transcript v0.3.1-alpha

Data: 2026-08-15
Canal: alpha
Status: correcao de performance na conversao MP3

## Resumo

Esta versao corrige a preparacao lenta de audio em videos longos. O app deixa de gerar um WAV gigante por padrao e passa a converter o arquivo para MP3 rapido, usando esse MP3 final como fonte da transcricao e do player.

## Principais mudancas

- Conversao para MP3 com `libmp3lame` em modo rapido.
- Remocao da etapa duplicada de WAV temporario no fluxo normal.
- Retry limpa `audio.mp3` e `transcription.wav` parciais quando existe arquivo original para reprocessar.
- O video original continua sendo descartado apos a conversao bem-sucedida.

## Validacao

- [x] `.venv\\Scripts\\python.exe -m compileall app`.
- [x] `npm run check:web`.
- [x] `npm run check:desktop`.
- [x] Benchmark em MP4 real de 378 MB: `prepare_audio` concluiu em 44,56s.
- [x] MP3 final criado e preservado para player/transcricao.
- [ ] Teste manual pelo app desktop com o mesmo arquivo real.
- [ ] Confirmar transcricao completa apos retry no app.

## Riscos conhecidos

- A transcricao passa a ler o MP3 final em vez do WAV temporario; o MP3 usa qualidade suficiente para fala, mas deve ser validado em audios ruins.
- O job que estava preso antes desta correcao pode precisar ser cancelado/retentado ou reiniciado pelo app.
