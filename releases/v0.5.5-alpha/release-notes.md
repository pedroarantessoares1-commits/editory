# Editory v0.5.5-alpha

Release Alpha para macOS Apple Silicon, preparada para compartilhamento externo sem dados locais do Pedro.

## O que mudou

- Remove caches Python gerados durante o empacotamento antes de criar os artefatos macOS.
- Mantem o app empacotado usando a area local de dados do usuario no macOS.
- Mantem a validacao do pacote para bloquear dados locais, uploads, jobs, `.env`, metadados Git e caches dentro dos ZIPs finais.

## Arquivo para instalar

Baixe o arquivo `.dmg` desta Release em um Mac Apple Silicon, abra o instalador e arraste o Editory para Applications.

## Observacao importante

Esta build Alpha ainda nao esta assinada/notarizada pela Apple. No primeiro uso, o macOS pode pedir liberacao manual em System Settings > Privacy & Security.

