# Editory v0.4.1-alpha

Patch de refinamento da experiencia de leitura da transcricao.

## Principais mudancas

- A visualizacao da copy agora abre em tema escuro por padrao.
- Foi adicionada uma alternancia entre tema Escuro e Branco na tela da transcricao.
- A escolha do tema fica salva localmente no navegador.

## Preservado

- Motor de transcricao local.
- Modelo Whisper, CUDA, FFmpeg e pipeline de audio.
- Segmentos e timestamps usados para SRT.
- Historico, tarefas, player, copiar texto limpo e modulo Remover Silencio.
- Tela de iniciamento/splash do Editory.

## Validacao

- `npm run check:web`: passou.
- `npm run check:desktop`: passou.
- `python -m py_compile app\\main.py app\\models.py app\\exporters.py app\\engine.py app\\transcriber.py app\\silence.py`: passou.
- `npm run release:check`: passou.
- Pagina servida em `/`: confirmou `V0.4.1 ALPHA` e controles `Escuro`/`Branco`.
- `/api/health`: passou com CUDA detectada.

## Pendencias conhecidas

- Validacao visual manual da alternancia de tema deve ser feita no app aberto.
