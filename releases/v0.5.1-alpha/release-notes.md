# Editory v0.5.1-alpha

Release de correcao focada na abertura do app pelo launcher local.

## Corrigido

- Corrigida a resolucao da raiz do projeto quando o app e aberto pelo `launcher\App Transcript\App Transcript.exe`.
- O app nao procura mais a `.venv` dentro da pasta `launcher\App Transcript\resources` quando esta rodando no modo launcher local.
- A interface principal carrega assim que o backend local esta disponivel, evitando travar na tela inicial enquanto o motor de transcricao aquece.

## Nao alterado

- Motor de transcricao.
- Modelo Whisper.
- CUDA/GPU.
- FFmpeg.
- Logica de processamento de arquivos.
- Historico, copy e exportacao SRT.
