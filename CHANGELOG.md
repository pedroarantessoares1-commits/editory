# Changelog

Todas as mudancas importantes do App Transcript ficam catalogadas aqui.

Formato usado: Adicionado, Alterado, Corrigido, Removido e Observacoes.

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
