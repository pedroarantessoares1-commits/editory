# App Transcript v0.3.0-alpha

Data: 2026-08-14
Canal: alpha
Status: exportacao SRT

## Resumo

Esta versao adiciona exportacao de legendas SRT para transcricoes concluidas. O arquivo usa os timestamps reais por segmento ja retornados pelo Whisper e pode ser baixado direto pela area de resultado da transcricao.

## Principais mudancas

- Endpoint local para baixar `.srt` de um job concluido.
- Botao `Exportar SRT` no painel de resultado da transcricao.
- Suporte a SRT traduzido para jobs criados com traducao.
- Nome do arquivo baseado no nome original do video/audio.
- Saida SubRip em UTF-8 com indices sequenciais e timestamps `HH:MM:SS,mmm`.
- Quebra visual do texto em linhas mais legiveis sem alterar palavras e sem criar timestamps artificiais.

## Checklist de release

- [x] Python compile.
- [x] `npm run check:web`.
- [x] `npm run check:desktop`.
- [x] `npm run release:check`.
- [ ] Testar exportacao SRT em transcricao curta.
- [ ] Testar exportacao SRT em arquivo de varios minutos.
- [ ] Testar acentos em portugues.
- [ ] Testar idioma estrangeiro.
- [ ] Testar job traduzido.
- [ ] Validar estrutura em editor/player compativel com SRT ou DaVinci Resolve.

## Riscos conhecidos

- O app ainda nao persiste timestamps por palavra, entao a exportacao usa os limites reais de cada segmento.
- Segmentos longos nao sao divididos em novos blocos temporais para evitar timestamps inventados.
- Validacao manual no DaVinci Resolve ainda precisa ser feita com arquivo real do usuario.
