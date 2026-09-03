# Editory v0.5.2-alpha

Release de empacotamento para facilitar o compartilhamento da versao macOS Apple Silicon.

## Adicionado

- Script `scripts/package-macos.sh` para gerar DMG/ZIP macOS arm64 e montar um pacote compartilhavel com notas, manifesto e checksums.
- Comando `npm run package:mac` para rodar o empacotador em um Mac ou no runner macOS do GitHub Actions.
- Workflow de Release passa a usar o empacotador macOS e anexar `SHA256SUMS-macos-arm64.txt`.

## Alterado

- Documentacao de distribuicao atualizada com o fluxo para gerar um pacote macOS e compartilhar com outra pessoa.
- Versao catalogada como `0.5.2-alpha`.

## Nao alterado

- Motor de transcricao.
- Modelo Whisper.
- CUDA/GPU.
- FFmpeg.
- Logica de processamento de arquivos.
- Historico, copy e exportacao SRT.
