# Editory v0.5.0-alpha

Release de infraestrutura para versionamento, distribuicao e updates.

## Principais mudancas

- Electron Builder configurado para builds locais e oficiais.
- Windows x64 preparado com instalador NSIS.
- macOS arm64 preparado com DMG/ZIP para Macs Apple Silicon.
- Workflow manual de GitHub Release com `workflow_dispatch`.
- Sistema de update em background com `autoDownload=false`.
- Indicador discreto `Nova atualizacao` no header.
- Modal de update com versao disponivel, versao instalada, notas e acoes.
- Windows baixa update somente apos clique do usuario e instala somente apos confirmacao.
- macOS Alpha abre o DMG/release para instalacao manual enquanto nao houver assinatura Apple.
- Documentacao de distribuicao em `docs/distribution.md`.

## Preservado

- Motor de transcricao local.
- Modelo Whisper, CUDA, FFmpeg e pipeline de audio/video.
- Historico, tarefas, copy limpa, SRT e Remover Silencio.
- Identidade visual atual do Editory.

## Validacao

- `npm install --save electron-updater semver`: passou.
- `npm install --save-dev electron-builder`: passou.
- `npm install --package-lock-only`: passou.
- `npm run check:web`: passou.
- `npm run check:desktop`: passou.
- Python compile: passou.
- `npm run release:check`: passou.
- `npm run build`: gerou `dist/win-unpacked/Editory.exe` com recursos essenciais.
- `npm run build:win`: iniciou empacotamento NSIS, mas estourou timeout local com runtime Python grande antes de finalizar o instalador.

## Limitacoes conhecidas

- Repositorio GitHub remoto ainda precisa ser criado/conectado.
- O conector GitHub disponivel nao expôs ferramenta de criacao de repositorio nesta sessao.
- GitHub Releases em repositorio privado nao podem ser consultados pelo app sem token; tokens nao devem ser embutidos no aplicativo.
- Build macOS arm64 precisa ser validado em runner/maquina macOS.
- Instalador NSIS Windows precisa ser gerado em ambiente sem timeout maior, preferencialmente GitHub Actions ou maquina dedicada.
- Assinatura Apple, notarizacao e assinatura Windows ficam para uma etapa futura com certificados reais.
