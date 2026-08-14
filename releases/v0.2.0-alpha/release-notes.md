# App Transcript v0.2.0-alpha

Data: 2026-08-13
Canal: alpha
Status: identidade visual inicial do Editory

## Resumo

Esta versao adiciona a splash/loading inicial do Editory, portada da referencia do Emergent e adaptada ao app local HTML/CSS/JS + Electron. A tela usa nome, slogan e paleta da identidade da marca, sem dependencias externas.

## Principais mudancas

- Splash/loading premium com fundo escuro em gradiente, glows roxo/indigo e grid sutil.
- Asset da marca recortado da identidade visual enviada, com fundo transparente.
- Nome `EDITORY` e slogan oficial: `O território de quem vive da edição.`
- Loader circular animado, barra de progresso e mensagens rotativas.
- Finalizacao com `Bora editar.` e fade out quando o motor fica pronto.
- Estado visual de erro para falhas no aquecimento do motor.
- Tela temporaria do Electron atualizada para a identidade Editory.
- Sem PostHog, Cloudflare, Tailwind CDN, Google Fonts ou scripts de preview do HTML do Emergent.

## Checklist de release

- [x] Python compile.
- [x] `npm run check:web`.
- [x] `npm run check:desktop`.
- [x] `npm run release:check`.
- [ ] Teste visual manual no app desktop.
- [ ] Recriar executavel portatil.
- [ ] Recriar atalho de desktop.

## Riscos conhecidos

- A marca foi gerada a partir da imagem de identidade enviada e pode ser substituida por um PNG/SVG oficial dedicado.
- O progresso da splash ainda usa simulacao visual enquanto o backend nao fornece progresso real detalhado.
- O executavel portatil existente pode continuar com metadados/atalho antigos ate ser recriado.
