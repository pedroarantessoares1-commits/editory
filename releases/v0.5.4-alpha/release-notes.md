# Editory v0.5.4-alpha

Release macOS Apple Silicon preparada para download e instalacao por outra pessoa, sem dados locais do Pedro.

## Corrigido

- Dependencias NVIDIA/CUDA agora ficam restritas a Linux no `requirements.txt`, evitando falha no build macOS.

## Mantido da preparacao macOS

- Workflow `Release macOS` publica uma GitHub Release macOS via execucao manual no GitHub Actions.
- Checagem de pacote limpo bloqueia `data/`, uploads, jobs, historico, `.env`, caches locais e metadados Git dentro dos ZIPs gerados.
- O app empacotado salva dados novos no espaco local do usuario do Electron.

## Para instalar no macOS

1. Baixe o arquivo `.dmg` da Release.
2. Abra o `.dmg`.
3. Arraste o Editory para Applications.
4. Abra o Editory.

## Privacidade do pacote

- A build e feita em runner limpo do GitHub Actions.
- A pasta local `data/` nao e versionada nem incluida no app.
- Historico, uploads, jobs, caches locais e `.env` nao entram no pacote.
- Ao abrir no Mac do seu amigo, o app cria um espaco novo de dados para ele.

## Observacao

- Esta build Alpha ainda nao tem assinatura/notarizacao Apple. No primeiro uso, o macOS pode exigir liberacao manual em Ajustes do Sistema.
