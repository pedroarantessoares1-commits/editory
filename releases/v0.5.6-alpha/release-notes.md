# Editory v0.5.6-alpha

Release Alpha para macOS Apple Silicon, preparada para compartilhamento externo sem dados locais do Pedro.

## O que mudou

- Exclui explicitamente `app/data`, uploads, jobs e caches Python dos recursos empacotados.
- Refina a validacao do pacote para bloquear dados locais do app sem confundir arquivos internos de bibliotecas Python.
- Mantem o app empacotado usando a area local de dados do usuario no macOS.

## Arquivo para instalar

Baixe o arquivo `.dmg` desta Release em um Mac Apple Silicon, abra o instalador e arraste o Editory para Applications.

## Observacao importante

Esta build Alpha ainda nao esta assinada/notarizada pela Apple. No primeiro uso, o macOS pode pedir liberacao manual em System Settings > Privacy & Security.

