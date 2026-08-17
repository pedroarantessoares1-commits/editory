# Distribuicao e Updates do Editory

## Desenvolvimento

```powershell
npm install
.\scripts\install.ps1
npm run dev
```

`npm run dev` apenas abre o app local. Ele nao publica release.

## Build Windows

```powershell
npm run build:win
```

Gera um instalador NSIS Windows x64 em `dist/`. O build local nao publica nada.

O instalador inclui os recursos do app e a pasta `.venv` local quando ela existir. Antes de buildar em uma maquina limpa, rode `.\scripts\install.ps1`.

## Build macOS Apple Silicon

Em um Mac Apple Silicon ou runner macOS:

```bash
npm install
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm run build:mac
```

Gera `.dmg` e `.zip` arm64 em `dist/`. O build atual e para testes Alpha sem assinatura/notarizacao Apple.

## Releases oficiais

Releases oficiais devem ser publicados apenas pelo workflow manual:

1. Atualize `package.json`, `package-lock.json`, `app/main.py`, `CHANGELOG.md` e `releases/vX.Y.Z-canal/`.
2. Configure `distribution/update-config.json` com `owner`, `repo` e `releaseUrl` quando o repositorio de releases estiver definido.
3. Commit e tag locais.
4. No GitHub: Actions -> Release -> Run workflow.
5. Informe a versao, titulo, prerelease e arquivo de notas.

Commits e pushes nao publicam release.

## Versionamento

Use SemVer:

- `0.5.0-alpha`: feature grande em alpha.
- `0.5.1-alpha`: correcao pequena em alpha.
- `0.6.0-beta`: beta quando os recursos principais estiverem prontos.
- `1.0.0`: primeira versao estavel.

O Electron le a versao principal de `package.json` via `app.getVersion()`.

## Updates

O app verifica updates em background alguns segundos depois de abrir a interface.

- Nao bloqueia inicializacao.
- Nao baixa automaticamente.
- Nao reinicia sem permissao.
- Nao mostra nada se nao houver update.
- Falhas silenciosas nao derrubam o app.

O indicador aparece no header apenas quando uma versao publicada mais recente existe.

## Windows

No Windows empacotado, o app usa `electron-updater` com `autoDownload = false`.

Fluxo:

1. Detecta GitHub Release publicada.
2. Mostra `Nova atualizacao`.
3. Usuario clica em `Atualizar agora`.
4. Download inicia e mostra progresso.
5. Quando pronto, o usuario clica em `Reiniciar e atualizar`.

## macOS Alpha sem assinatura

Sem Developer ID Application e notarizacao, nao tentamos substituir o `.app` automaticamente.

Fluxo atual:

1. Detecta GitHub Release publicada.
2. Mostra `Nova atualizacao`.
3. Usuario clica em `Baixar atualizacao`.
4. O app abre o `.dmg` arm64 ou a pagina oficial do release.
5. Usuario instala/substitui manualmente.

## Repositorio privado

GitHub Releases em repositorio privado exigem autenticacao para consulta/download. Nao coloque tokens no app.

Opcoes seguras:

- manter o codigo privado, mas publicar releases em um repositorio/feed publico separado;
- usar uma infraestrutura de update autenticada propria;
- durante Alpha interno, distribuir links pelo GitHub para usuarios autenticados.

## Assinatura futura

Quando tivermos credenciais:

- macOS: adicionar Developer ID Application, Hardened Runtime, entitlements, notarizacao e secrets no GitHub Actions.
- Windows: adicionar certificado de code signing e secrets no GitHub Actions.
- Depois da assinatura macOS, substituir o fluxo manual por auto-update completo suportado.

## Teste do updater

1. Instale uma versao antiga, por exemplo `0.5.0-alpha`.
2. Publique manualmente uma release maior, por exemplo `0.5.1-alpha`.
3. Abra a versao antiga.
4. Confirme que aparece `Nova atualizacao`.
5. Windows: baixar, ver progresso, reiniciar e confirmar versao.
6. macOS: abrir/baixar DMG arm64, instalar manualmente e confirmar versao.
