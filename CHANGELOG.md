# Changelog

Todas as mudancas importantes do App Transcript ficam catalogadas aqui.

Formato usado: Adicionado, Alterado, Corrigido, Removido e Observacoes.

## [0.5.6-alpha] - 2026-09-03

### Corrigido

- Configuracao do pacote macOS exclui explicitamente `app/data`, uploads, jobs e caches Python dos recursos empacotados.
- Verificacao da Release macOS passa a bloquear dados locais do app sem confundir pastas `data` internas de dependencias Python.

### Observacoes

- Mantem a publicacao manual pelo workflow `Release macOS`.
- Build macOS ainda segue sem assinatura/notarizacao Apple nesta fase Alpha.

## [0.5.5-alpha] - 2026-09-03

### Corrigido

- Empacotador macOS remove caches Python (`__pycache__`, `.pyc` e `.pyo`) do runtime antes de gerar os artefatos.

### Observacoes

- Mantem a checagem anti-dados locais no workflow `Release macOS`, incluindo bloqueio de caches dentro dos ZIPs finais.
- Build macOS ainda segue sem assinatura/notarizacao Apple nesta fase Alpha.

## [0.5.4-alpha] - 2026-09-03

### Corrigido

- Dependencias NVIDIA/CUDA ficam restritas a Linux no `requirements.txt`, evitando falha de instalacao no runner macOS.

### Observacoes

- Mantem o fluxo da `Release macOS` com pacote limpo, checagem anti-dados locais e armazenamento por usuario no app empacotado.
- Build macOS ainda segue sem assinatura/notarizacao Apple nesta fase Alpha.

## [0.5.3-alpha] - 2026-09-03

### Adicionado

- Workflow `Release macOS` para publicar uma GitHub Release macOS via execucao manual no GitHub Actions.
- Checagem de pacote limpo no runner macOS para bloquear `data/`, uploads, jobs, historico, `.env`, caches locais e metadados Git dentro dos ZIPs gerados.

### Alterado

- App empacotado passa a salvar dados novos no espaco local do usuario do Electron, evitando escrita dentro dos recursos do app e garantindo instalacao zerada para outra pessoa.
- Documentacao de distribuicao registra que o pacote nao inclui dados locais do Pedro.

### Observacoes

- Build macOS ainda segue sem assinatura/notarizacao Apple nesta fase Alpha.
- Motor de transcricao, modelos de IA, CUDA, FFmpeg e processamento local nao foram alterados.

## [0.5.2-alpha] - 2026-09-03

### Adicionado

- Empacotador macOS em `scripts/package-macos.sh` para gerar DMG/ZIP arm64 e montar um pacote compartilhavel com notas, manifesto e checksums.
- Comando `npm run package:mac` para uso local em um Mac ou no runner macOS do GitHub Actions.

### Alterado

- Workflow manual de Release passa a usar o empacotador macOS e anexar os checksums do pacote.
- Documentacao de distribuicao atualizada com um fluxo direto para compartilhar a build macOS com outra pessoa.
- Configuracao de updates passa a apontar para o repositorio publico `pedroarantessoares1-commits/editory`.

### Observacoes

- Build macOS ainda requer Mac/runner macOS e segue sem assinatura/notarizacao Apple nesta fase Alpha.
- Motor de transcricao, modelos de IA, CUDA, FFmpeg e processamento local nao foram alterados.

## [0.5.1-alpha] - 2026-08-26

### Corrigido

- Corrigida a abertura pelo launcher/atalho, que podia procurar a `.venv` no caminho errado do Electron portatil.
- A tela principal agora abre assim que o backend local responde, sem ficar bloqueada aguardando o aquecimento completo do motor de IA.

### Observacoes

- Motor de transcricao, modelo Whisper, CUDA, FFmpeg e processamento local nao foram alterados.

## [0.5.0-alpha] - 2026-08-17

### Adicionado

- Infraestrutura inicial de distribuicao com Electron Builder.
- Configuracao de build Windows x64 com instalador NSIS.
- Configuracao de build macOS arm64 com DMG/ZIP para Apple Silicon.
- Workflow manual de GitHub Release via `workflow_dispatch`, sem publicacao automatica por push ou commit.
- Preload seguro com API restrita para updates.
- Servico de updates no processo Main com `electron-updater`, `autoDownload=false` e comparacao SemVer.
- Indicador discreto de nova atualizacao e modal de update na interface.
- Fluxo Windows para baixar update somente apos consentimento e instalar somente apos confirmacao.
- Fluxo macOS Alpha seguro, abrindo o DMG/release manualmente enquanto nao houver assinatura Apple.
- Documentacao tecnica em `docs/distribution.md`.

### Alterado

- Caminhos do Electron agora diferenciam desenvolvimento e app empacotado para carregar recursos em `process.resourcesPath`.
- `.gitignore` reforcado para builds, caches, logs, certificados, credenciais e artefatos gerados.
- `README.md` atualizado com comandos de desenvolvimento/build e referencia de distribuicao.

### Observacoes

- Motor de transcricao, modelos de IA, CUDA, FFmpeg e processamento local nao foram alterados.
- Repositorio GitHub remoto ainda precisa ser criado/conectado; nao havia remoto configurado no projeto.
- Updates via GitHub Releases privados nao usam token no app por seguranca. Para update automatico real, use releases publicos ou feed seguro dedicado.
- Assinatura Apple, notarizacao e code signing Windows ficaram preparados/documentados, mas nao configurados por falta de certificados.

## [0.4.1-alpha] - 2026-08-17

### Adicionado

- Alternancia de tema claro/escuro na visualizacao da copy.
- Preferencia do tema da copy salva localmente no navegador.

### Alterado

- Visualizacao da copy passa a abrir em tema escuro por padrao, mantendo o fundo branco como opcao.

### Observacoes

- Ajuste limitado a interface de leitura da transcricao; motor, CUDA, FFmpeg, SRT e processamento local nao foram alterados.
- Tela de iniciamento/splash do Editory foi revisada e mantida no fluxo atual.

## [0.4.0-alpha] - 2026-08-17

### Adicionado

- Nova interface Editory para o modulo de transcricao, com header compacto, navegacao segmentada, paineis responsivos e cards de historico.
- Visualizacao interna dedicada para leitura da transcricao como documento/copy, aberta a partir do historico.
- Busca movida para a visualizacao da copy, com destaque de ocorrencias e contagem de resultados.
- Feedback visual discreto ao copiar texto.

### Alterado

- Historico de transcricoes saiu da coluna lateral e passou a ficar abaixo da area principal de processamento.
- Tarefas ativas agora ficam separadas do historico concluido na tela de transcricao.
- Botao de copiar passa a gerar texto natural a partir dos segmentos, sem timestamps, IDs ou metadados.
- Responsividade geral revisada para evitar overflow horizontal em janelas menores.
- Janela desktop passa a permitir largura minima menor para acomodar o novo layout responsivo.

### Observacoes

- O motor de transcricao, modelo Whisper, CUDA, FFmpeg, pipeline local e geracao de SRT nao foram alterados.
- A exportacao SRT continua usando os timestamps reais dos segmentos persistidos.
- O modulo Remover Silencio recebeu apenas tratamento visual global, sem mudanca de logica interna.

## [0.3.1-alpha] - 2026-08-15

### Corrigido

- Preparacao de audio deixou de gerar um WAV gigante por padrao antes da transcricao.
- Conversao para MP3 agora usa encoder rapido e evita filtros pesados no arquivo do player.
- Retry remove MP3/WAV parciais de tentativas travadas antes de reprocessar.

### Alterado

- O MP3 final passa a ser a fonte da transcricao, mantendo o video descartavel apos a conversao.
- Mensagem de preparo agora indica conversao rapida para MP3.

### Observacoes

- Benchmark no arquivo real `ProstaLiv_-_Apresentacao_Oficial.mp4`: preparo completo caiu para aproximadamente 44,56s.
- O processo antigo fazia etapas duplicadas e podia aparentar travamento em videos longos.

## [0.3.0-alpha] - 2026-08-14

### Adicionado

- Exportacao SRT para transcricoes concluidas usando timestamps reais dos segmentos do Whisper.
- Botao "Exportar SRT" na area de resultado da transcricao.
- Suporte a SRT traduzido quando o job foi criado com `task="translate"`, mantendo os timestamps originais.
- Catalogo de release em `releases/v0.3.0-alpha`.

### Alterado

- Gerador SRT agora corrige arredondamento de milissegundos, ignora trechos vazios e quebra texto em linhas de leitura sem inventar timestamps.
- Metadata FastAPI e pacote atualizadas para `0.3.0-alpha`.

### Observacoes

- A exportacao usa timestamps por segmento, porque o app ainda nao persiste timestamps por palavra.
- Nenhuma logica de transcricao, traducao, modelo ou pipeline de audio foi alterada.

## [0.2.0-alpha] - 2026-08-13

### Adicionado

- Splash/loading inicial do Editory baseada na referencia visual do Emergent.
- Asset de marca recortado da identidade visual enviada, com fundo transparente.
- Loader circular, barra de progresso, mensagens rotativas, mensagem final "Bora editar." e fade out.
- Responsividade da splash para mobile, desktop e ultrawide.
- Suporte a `prefers-reduced-motion` e atributos acessiveis para status/progresso.
- Tela temporaria do Electron com identidade Editory antes do backend carregar.

### Alterado

- Titulo da janela e metadata FastAPI passam a usar Editory nesta versao.
- Loading inicial agora acompanha o estado real do motor e usa progresso simulado apenas enquanto nao ha progresso real.

### Corrigido

- Estado de falha do motor agora permanece visivel na splash, evitando loading infinito silencioso.

### Observacoes

- A marca foi gerada a partir da imagem de identidade enviada e pode ser substituida por um PNG/SVG oficial dedicado.
- O executavel portatil nao foi recriado nesta etapa.

## [0.1.0-alpha] - 2026-08-13

### Adicionado

- App desktop local com Electron e backend FastAPI iniciado automaticamente.
- Transcricao local com `faster-whisper`, fila sequencial, GPU CUDA quando disponivel e fallback para CPU.
- Tela de loading do motor, aquecimento inicial e stand-by apos inatividade.
- Upload acumulativo de varios audios/videos antes de executar.
- Conversao de video/audio para MP3 e descarte do video original apos preparacao.
- Historico, lista de tarefas, retry, cancelar tarefa e limpar lista.
- Player sincronizado com trechos da transcricao e botao "Copiar tudo".
- Ferramenta separada "Remover Silencio" com tarefas e historico proprios.
- Removedor de silencio local com estrategias Inteligente, Voz Protegida e Volume Agressivo.
- Catalogo inicial de release em `releases/v0.1.0-alpha`.

### Alterado

- Removedor de silencio passou a usar volume adaptativo como decisao principal e Silero VAD como protecao.
- UI mantida simples para priorizar estabilidade e codigo antes do design final.

### Corrigido

- Fallback CUDA/CPU para evitar falha quando DLLs CUDA/cuBLAS/cuDNN estiverem indisponiveis.
- Evita carregar o modelo Whisper a cada video.

### Observacoes

- Versao alpha: funcional para uso local, mas ainda precisa calibracao com audios reais.
- Proxima meta sugerida: `0.2.0-alpha`, focada em calibrar remover silencio no caso real `4:09 -> ~3:49`.
