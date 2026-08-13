# Project Memory: App Transcript

## Versioning Rule

- Sempre que houver uma alteracao grande, criar uma nova versao do app.
- Tambem criar nova versao quando o usuario pedir explicitamente "criar nova versao", "catalogar versao", "fechar release" ou equivalente.
- Mudancas grandes incluem:
  - novo motor ou mudanca relevante no motor de transcricao;
  - mudanca relevante no removedor de silencio;
  - nova janela/ferramenta;
  - mudanca grande de design/frontend;
  - mudanca de empacotamento/executavel/atalho;
  - alteracao de fluxo de dados, historico, tarefas ou armazenamento;
  - correcao critica de travamento, perda de dados ou falha de GPU/CPU.

## Release Checklist

Antes de catalogar uma versao:

1. Atualizar versao em `package.json`, `package-lock.json` e `app/main.py`.
2. Atualizar `CHANGELOG.md`.
3. Criar ou atualizar `releases/vX.Y.Z[-canal]/release-notes.md`.
4. Criar ou atualizar `releases/vX.Y.Z[-canal]/manifest.json`.
5. Rodar `npm run release:check`.
6. Recriar executavel/atalho se a mudanca afetar desktop, build ou runtime.
7. Fazer commit.
8. Criar tag Git `vX.Y.Z[-canal]`.

## Version Defaults

- Use `alpha` enquanto o app ainda estiver mudando bastante.
- Use `beta` quando recursos principais estiverem prontos e faltar polimento/testes.
- Use `stable` ou sem sufixo apenas quando estiver confiavel para uso diario.
- Para feature grande, subir minor: `0.1.0-alpha` -> `0.2.0-alpha`.
- Para correcao pequena, subir patch: `0.2.0-alpha` -> `0.2.1-alpha`.
