# App Transcript v0.1.0-alpha

Data: 2026-08-13
Canal: alpha
Status: baseline local catalogada

## Resumo

Primeira versao catalogada do App Transcript. Inclui app desktop local, transcricao com Whisper/faster-whisper, historico, tarefas, player sincronizado e ferramenta de remover silencio com estrategias locais.

## Principais recursos

- App desktop por Electron com backend Python/FastAPI local.
- Transcricao local com GPU CUDA quando disponivel e CPU como fallback.
- Motor de transcricao aquecido ao abrir e stand-by apos 20 minutos sem uso.
- Upload acumulativo de arquivos de varias pastas.
- Historico e tarefas separados para Transcricao e Remover Silencio.
- Player de audio, trechos sincronizados e copiar transcricao completa.
- Removedor de silencio local com estrategias:
  - Inteligente;
  - Voz Protegida;
  - Volume Agressivo.

## Checklist de release

- [x] Python compile.
- [x] `npm run check:web`.
- [x] `npm run check:desktop`.
- [x] `/api/health`.
- [x] App desktop abre e inicia backend.
- [x] Executavel portatil criado.
- [x] Atalho de desktop criado.
- [ ] Teste manual longo com lote real.
- [ ] Calibracao com audio real `4:09 -> ~3:49`.

## Riscos conhecidos

- Remover silencio ainda precisa calibracao com audios reais do usuario.
- Design ainda e provisorio.
- Executavel atual e portatil e depende da pasta do projeto continuar no mesmo local.
- Modelos e dependencias pesadas ficam fora do Git.

## Proxima versao sugerida

`v0.2.0-alpha`: calibracao fina do removedor de silencio com casos reais e comparacao por duracao, cortes e escuta.
