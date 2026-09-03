# Editory v0.5.3-alpha

Release macOS Apple Silicon preparada para compartilhamento externo limpo.

## Adicionado

- Workflow `Release macOS`, que publica uma GitHub Release macOS via execucao manual no GitHub Actions.
- Checagem de pacote limpo no runner macOS para bloquear `data/`, uploads, jobs, historico, `.env`, caches locais e metadados Git dentro dos ZIPs gerados.

## Alterado

- O app empacotado passa a salvar dados novos no espaco local do usuario do Electron, em vez de tentar usar a pasta interna dos recursos do app.
- Versao catalogada como `0.5.3-alpha`.

## Para instalar no macOS

1. Baixe o arquivo `.dmg` da Release.
2. Abra o `.dmg`.
3. Arraste o Editory para Applications.
4. Abra o Editory.

## Privacidade do pacote

- A build e feita em runner limpo do GitHub Actions.
- A pasta local `data/` nao e versionada nem incluida no app.
- Historico, uploads, jobs, caches locais e `.env` nao entram no pacote.

## Observacao

- Esta build Alpha ainda nao tem assinatura/notarizacao Apple. No primeiro uso, o macOS pode exigir liberacao manual em Ajustes do Sistema.
