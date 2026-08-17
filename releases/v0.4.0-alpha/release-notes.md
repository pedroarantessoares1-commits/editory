# Editory v0.4.0-alpha

Release focada no redesign completo da experiencia do modulo de Transcricao.

## Principais mudancas

- Interface reconstruida com identidade visual Editory, mantendo a stack atual de HTML, CSS e JavaScript.
- Header mais compacto, status tecnico discreto e navegacao em tabs segmentadas.
- Area principal focada em upload, configuracoes e tarefas ativas.
- Historico movido para baixo da area principal, em cards responsivos.
- Transcricao completa removida da home e aberta em uma segunda view interna.
- View da copy formatada como documento de leitura, com busca, copiar texto e exportar SRT.
- Copia limpa reconstruida a partir dos segmentos, sem timestamps ou metadados.
- Minimo da janela Electron reduzido para melhorar o uso em janelas menores.

## Preservado

- Motor de transcricao local.
- Modelo Whisper configurado pelo app.
- CUDA, fallback CPU, FFmpeg e pipeline de audio.
- Segmentos e timestamps usados para SRT.
- Historico local.
- Upload multiplo, fila, retry, cancelar, player e modulo Remover Silencio.

## Validacao

- `npm run check:web`: passou.
- `npm run check:desktop`: passou.
- `python -m py_compile app\\main.py app\\models.py app\\exporters.py app\\engine.py app\\transcriber.py app\\silence.py`: passou.
- Backend local em `http://127.0.0.1:8765`: respondeu com status 200 para `/`, `/styles.css` e `/api/history/transcriptions`.
- Arquivo real `audio.mp3` reprocessado a partir de historico local: concluido com 32 segmentos, idioma `pt` e duracao de 95,64s.
- Exportacao SRT validada no job reprocessado, preservando timestamps reais.

## Pendencias conhecidas

- Validacao visual com navegador real/Playwright nao foi executada porque nao havia navegador/headless tool disponivel no ambiente.
- Copia real do clipboard deve ser validada no app aberto, porque o ambiente atual nao oferece controle visual/clipboard de navegador.
